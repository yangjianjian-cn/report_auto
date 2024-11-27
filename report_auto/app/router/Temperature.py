__coding__ = "utf-8"

import json
import logging
import os
import re
from collections import defaultdict

from asammdf import MDF
from asammdf.blocks.utils import MdfException
from flask import request, jsonify, render_template
from werkzeug.utils import secure_filename

from app import db_pool, env_input_path
from app.router import temperature_bp
from app.service.TemperatureDataService import measurement_file_save, batch_chip_dict_save, \
    get_tool_dictionary_details, get_chip_dict, get_measurement_file_list_page, get_measurement_file_list, \
    chip_dict_in_sql, temperature_variables_edit, process_temperature_data
from app.service.TemperatureListService import chip_dict_del
from app.service.TemperatureWorkTimeService import relative_difference, temperature_duration
from pojo.TemperatureVariable import TemperatureVariable
from tools.utils.DBOperator import create_table, batch_insert_data, delete_from_tables, \
    alter_table_add_columns, update_table
from tools.utils.FileUtils import get_filename_without_extension
from tools.utils.HtmlGenerator import generate_select_options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# ################################################################数据采集#######################################
@temperature_bp.route('/index', methods=['GET'])
def temperature_upload():
    try:
        # 燃料类型
        measurement_file_source_list = get_tool_dictionary_details(dict_type='file_source')
        measurement_file_oem_list = get_tool_dictionary_details(dict_type='OEM_TYPE')
    except Exception as e:
        logging.error(f'查询异常:{e}')
        return render_template('error.html', failure_msg=f'{e}')
    return render_template('temperature_uploader.html',
                           measurement_file_source_list=measurement_file_source_list,
                           measurement_file_oem_list=measurement_file_oem_list)


@temperature_bp.route('/upload', methods=['POST'])
def upload():
    client_ip = getClientIp()

    # 1.获取上传文件和相关参数
    file = request.files.get('file')
    chunk_index = int(request.form.get('chunk', 0))
    total_chunks = int(request.form.get('chunks', 1))
    file_name = secure_filename(request.form.get('name'))
    test_team = secure_filename(request.form.get('test_team'))

    # 记录关键参数的日志
    logging.info(f"Received upload request from IP: {client_ip}")
    logging.info(
        f"Chunk index: {chunk_index}, Total chunks: {total_chunks}, File name: {file_name}, Test team: {test_team}")

    # 构建保存路径
    input_path = os.path.join(env_input_path, test_team, client_ip)
    if not os.path.exists(input_path):
        os.makedirs(input_path, exist_ok=True)

    # 2.合并文件
    save_file = ''
    msg = ''
    try:
        # 保存分片文件
        temp_file_path = os.path.join(input_path, f'{file_name}.part{chunk_index}')
        file.save(temp_file_path)

        # 如果是最后一个分片，则合并文件
        if chunk_index == total_chunks - 1:
            save_file = merge(file_name, total_chunks, input_path)
    except Exception as e:
        msg = f'{e}'
        logging.error(f'file saved err: {msg}')
        return jsonify({'status': 'failure', 'save_file': '', 'msg': msg})

    # 3.项目信息保存到数据库
    params: dict = {
        "source": request.form.get('fuel_type'),
        "project_name": request.form.get('project_name'),
        "ecu_hw": request.form.get('ecu_hw'),
        "oem": request.form.get('oem'),
        "vehicle_model": request.form.get('vehicle_model'),
        "vehicle_number": request.form.get('vehicle_number'),
        "sap_number": request.form.get('sap_number'),
        "software": request.form.get('software'),
        "file_name": get_filename_without_extension(file_name)
    }
    operation_code, operation_result = measurement_file_save(params=params)

    if "success" != operation_code:
        return jsonify({'status': 'failure', 'save_file': '', 'msg': operation_result})

    return jsonify({'status': 'success', 'save_file': save_file, 'msg': operation_result})


@temperature_bp.route('/configuration/page', methods=['GET'])
def temperature_configuration_add_page():
    s_oem = request.args.get("oem")
    chip_dict_list: list[dict] = get_chip_dict(s_oem)
    return render_template('temperature_configuration_add.html', s_oem=s_oem, chip_dict_list=chip_dict_list)


@temperature_bp.route('/configuration/add', methods=['POST'])
def temperature_configuration_add():
    try:
        s_oem = request.args.get("OEM")
        # 获取前端传递的数据
        data = request.get_json()
        operator_result, operator_msg = batch_chip_dict_save(data, s_oem)
        # 返回成功响应
        return jsonify({"success": operator_result, "message": operator_msg})
    except Exception as e:
        # 返回错误响应
        return jsonify({"success": False, "message": str(e)})


@temperature_bp.route('/configuration/del', methods=['POST'])
def temperature_configuration_del():
    try:
        # 获取请求体中的数据
        data = request.get_json()
        delete_ids = data.get('deleteIds', [])

        if not isinstance(delete_ids, list) or len(delete_ids) == 0:
            return jsonify({'message': 'Invalid or empty deleteIds array'}), 400

        trueOrFalse, trueOrFalseMsg = chip_dict_del(delete_ids)
        # 返回成功响应
        return jsonify({'message': trueOrFalseMsg}), 200 if trueOrFalse else 500

    except Exception as e:
        return jsonify({'message': f'Request error: {str(e)}'}), 500


@temperature_bp.route('/todb', methods=['POST'])
def todb():
    data = request.get_json()
    file_source = data['file_source']
    measure_file_path = data['save_file']

    last_id: str = data['save_file_id']
    if '' == last_id:
        return jsonify({'generate_report_failed': 'File number acquisition exception'})
    logging.info(f"文件元信息索引:{last_id}")

    # 1.采集测量数据
    selected_columns_dict: list[dict] = get_chip_dict(last_id)
    if len(selected_columns_dict) == 0:
        return jsonify({'generate_report_failed': "unconfigured acquisition volume"})

    selected_columns = [d['measured_variable'] for d in selected_columns_dict]
    logging.info(f"[信号量]已配置:{selected_columns}")

    mdf = MDF(measure_file_path)
    channels_db_keys = mdf.channels_db.keys()
    logging.info(f"[信号量]待采集:{channels_db_keys}")

    existing_columns = list(set(col for col in selected_columns if col in channels_db_keys))
    if "TECU_t" in channels_db_keys:
        existing_columns.append("TECU_t")
    elif "TECU_tRaw" in channels_db_keys:
        existing_columns.append("TECU_tRaw")
    logging.info(f"[信号量]可采集:{existing_columns}")

    try:
        df = mdf.to_dataframe(channels=existing_columns)
    except MdfException as e:
        logging.error(f"Error converting to DataFrame: {e}")
        return jsonify({'generate_report_failed': {e}})

    # 2. 数据清洗
    # 重命名DataFrame中的列
    df.columns = [rename_columns(col) for col in df.columns]
    column_names = df.columns.tolist()

    # 再进一步重命名
    rename_mapping = get_rename_mapping(column_names)
    logging.info(f"信号列和数据库列映射:{rename_mapping}")
    df.rename(columns=rename_mapping, inplace=True)  # 重命名列名

    # 去除连续的重复行
    # 首先对 DataFrame 进行排序，确保按时间顺序排列
    df.sort_values(by='timestamps', inplace=True)
    logging.debug(f"数据排序:{len(df)}")
    # 使用 keep='first' 选项保留第一次出现的非重复行
    df.drop_duplicates(keep='first', inplace=True)
    logging.debug(f"数据去重:{len(df)}")

    # 3.数据保存
    # 更新measurement_file，特殊列，(相对关系)
    params: dict = {}
    if 'DS_FILES' == file_source:
        tmp_dict: dict = {}
        tmp_dict["timestamps"] = "timestamps"
        tmp_dict["TECU_t"] = "TECU_t"
        params['special_columns'] = json.dumps(tmp_dict)
    elif 'NG_FILES' == file_source:
        ng_files_str: str = 'timestamps'  # TC1_Th9即X3, 各芯片与X3的相对关系

        tmp_dict: dict = {}

        tmp_dict["timestamps"] = "timestamps"

        if 'TECU_t' in rename_mapping:
            tmp_dict["TECU_t"] = "TECU_t"

        result: dict = {item['chip_name']: item['measured_variable'] for item in selected_columns_dict}
        if result.get("X3") in rename_mapping:
            tmp_dict["X3"] = result.get("X3")

        if result.get("X2") in rename_mapping:
            tmp_dict["X2"] = result.get("X2")

        params['special_columns'] = json.dumps(tmp_dict)

    where_params = {'id': last_id}
    update_table(db_pool, table='measurement_file', set_params=params, where_params=where_params)

    # 创建表
    table_name = 'chip_temperature'
    params: dict = {'file_id': last_id, 'source': file_source}
    c_ret_msg, columns_in_db = create_table(db_pool, table_name=table_name, df=df)
    if c_ret_msg != 'success':
        return jsonify({'generate_report_failed': {c_ret_msg}})

    # 找出 rename_mapping 中不在 columns_in_db 中的键
    missing_columns = [value for value in rename_mapping.values() if value not in columns_in_db]
    logging.info(f"表{table_name}添加列:{missing_columns}")
    if len(missing_columns) >= 1:
        op_flag, op_msg = alter_table_add_columns(db_pool, table=table_name, columns=missing_columns,
                                                  column_type="double")
        logging.info(f"{op_flag},{op_msg}")

    # 批量插入表
    i_ret_msg = batch_insert_data(db_pool, table_name=table_name, params=params, df=df)
    if i_ret_msg != 'success':
        return jsonify({'generate_report_failed': {i_ret_msg}})

    return jsonify({'generate_report_failed': ''})


# ################################################################数据分析#######################################
@temperature_bp.route('/list', methods=['GET'])
def temperature_list():
    return render_template('temperature_list.html')


@temperature_bp.route('/list/page', methods=['GET'])
def temperature_list_page():
    try:
        # 获取分页参数
        pageNum = int(request.args.get('pageNum', 1))  # 默认值为 1
        pageSize = int(request.args.get('pageSize', 10))  # 默认值为 10

        oem = request.args.get('oem', '')
        if oem:
            qryParam: dict[str] = {"oem": oem}
        else:
            qryParam: dict[str] = None

        # 计算数据库查询的起始位置和结束位置
        start = (pageNum - 1) * pageSize
        end = start + pageSize

        # 调用函数获取分页数据
        total_count, measurement_file_list = get_measurement_file_list_page(start=start, end=end, query_params=qryParam)

        # 构建响应数据
        response_data = {
            "code": 200,
            "msg": "success",
            "total": total_count,
            "data": measurement_file_list
        }

        return jsonify(response_data)

    except Exception as e:
        logging.error(f'查询异常: {e}')
        return render_template('error.html', failure_msg=str(e))


@temperature_bp.route('/delete_file', methods=['POST'])
def delete_file():
    data = request.get_json()
    file_id = data.get('id')

    try:
        # 调用数据库模块删除文件
        primary_table_name = 'measurement_file'
        primary_param: map = {'id': file_id}

        second_table_name = 'chip_temperature'
        second_param: map = {'file_id': file_id}

        result, message = delete_from_tables(db_pool, table=primary_table_name,
                                             param=primary_param)
        if result:
            result, message = delete_from_tables(db_pool, table=second_table_name,
                                                 param=second_param)
            if result:
                return jsonify({'success': True, 'message': '文件删除成功'})
            else:
                return jsonify({'success': False, 'message': '文件删除失败'})
        else:
            return jsonify({'success': False, 'message': '文件删除失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@temperature_bp.route('/configuration/list', methods=['GET'])
def temperature_configuration():
    measurement_file_id = request.args.get("file_id")
    return render_template('temperature_configuration_list.html', measurement_file_id=measurement_file_id)


@temperature_bp.route('/configuration_data', methods=['GET'])
def temperature_configuration_data():
    measurement_file_id: str = request.args.get('measurement_file_id')
    configuration_data_list: list[dict] = get_chip_dict(measurement_file_id)
    # 构建响应数据
    response_data = {
        "code": 200,
        "msg": "success",
        "data": configuration_data_list
    }
    return jsonify(response_data)


@temperature_bp.route('/quantitative/page', methods=['GET'])
def temperature_variable_page():
    measurement_file_id: str = request.args.get("file_id")
    measurement_file_list: list[dict] = get_measurement_file_list(measurement_file_id)

    if len(measurement_file_list) > 0:
        measurement_file = measurement_file_list[0]
        quantitative_variable = measurement_file.get("quantitative_variable") or ""
        statistical_variable = measurement_file.get("statistical_variable") or ""
        remark = measurement_file.get("remark") or ""
    else:
        quantitative_variable = ""
        statistical_variable = ""
        remark = ""
    return render_template('temperature_variables_page.html', measurement_file_id=measurement_file_id,
                           quantitative_variable=quantitative_variable,
                           statistical_variable=statistical_variable,
                           remark=remark)


@temperature_bp.route('/quantitative/edit', methods=['POST'])
def temperature_variable_edit():
    # 获取 JSON 数据
    data = request.get_json()
    # 检查是否成功获取 JSON 数据
    if not data:
        return jsonify({"success": False, "message": "Invalid JSON data"}), 400

    # 获取表单数据
    measurement_file_id = data.get("measurement_file_id")
    quantitative_variable = data.get('quantitative_variable')
    statistical_variable = data.get('statistical_variable')
    remarks = data.get('remark')

    # 验证数据（这里只是一个简单的检查，你可以根据实际需求进行更详细的验证）
    if not quantitative_variable or not statistical_variable:
        return jsonify({'success': False,
                        'message': "quantitative_variable field or statistical_variable field  is required"}), 400

    temperatureVariable = TemperatureVariable(
        measurement_file_id=measurement_file_id,
        quantitative_variable=quantitative_variable,
        statistical_variable=statistical_variable,
        remark=remarks
    )
    logging.info(f"temperature_variable_edit:{temperatureVariable}")

    operation_rlt, operation_msg = temperature_variables_edit(temperatureVariable)
    if operation_rlt:
        return jsonify({'success': True, 'message': 'success'}), 200
    else:
        return jsonify({'success': False, 'message': operation_msg}), 200


# ################################################################数据详情页#######################################
@temperature_bp.route('/details', methods=['GET'])
def temperature_details():
    selected_ids = []
    fileId = request.args.get('fileId')

    # 1.获取测量文件列表
    try:
        measurement_file_list = get_measurement_file_list(fileId=fileId)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    # 定量变量(离散图，求两个变量的线性关系)
    filtered_files: list = []
    quantitative_variable_list: list = []
    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
        filtered_files = [file for file in measurement_file_list if file['id'] in selected_ids]
    else:
        selected_ids.append(measurement_file_list[0].get('id'))
        filtered_files.append(measurement_file_list[0])

    for file_info in filtered_files:
        special_columns_str = file_info.get('quantitative_variable', '')
        if special_columns_str:
            quantitative_variable_list.append(special_columns_str)
    quantitative_variable_list = list(set(quantitative_variable_list))

    measurement_source = filtered_files[0].get('source')
    oem = filtered_files[0].get("oem")

    logging.info(f"定量变量:{quantitative_variable_list}")
    logging.info(f"燃料类型:{measurement_source}")
    logging.info(f"测量项目:{oem}")
    logging.info(f"观测文件:{selected_ids}")

    # 2. 获取芯片字典列表
    r_chip_dict: list[dict] = chip_dict_in_sql(selected_ids=selected_ids, project_type=oem)
    kv_chip_dict: dict = {item['measured_variable']: item['chip_name'] for item in r_chip_dict}
    measured_variables_list: list[str] = [item['measured_variable'] for item in r_chip_dict]
    logging.info(f"可观测信号量:{measured_variables_list}")

    # 离散图和折线图
    # DC1_Th
    selected_columns_dc1, temperature_time_dc1, data_structure_dc1 = process_temperature_data(
        prefix='DC1_',
        measured_variables_list=measured_variables_list,
        quantitative_variable_list=quantitative_variable_list,
        selected_ids=selected_ids,
        kv_chip_dict=kv_chip_dict
    )

    # TC1_Th
    selected_columns_tc1, temperature_time_tc1, data_structure_tc1 = process_temperature_data(
        prefix='TC1_',
        measured_variables_list=measured_variables_list,
        quantitative_variable_list=quantitative_variable_list,
        selected_ids=selected_ids,
        kv_chip_dict=kv_chip_dict
    )

    # TC2_Th
    selected_columns_tc2, temperature_time_tc2, data_structure_tc2 = process_temperature_data(
        prefix='TC2_',
        measured_variables_list=measured_variables_list,
        quantitative_variable_list=quantitative_variable_list,
        selected_ids=selected_ids,
        kv_chip_dict=kv_chip_dict
    )

    # 下拉复选框
    multi_select_html = generate_select_options(get_measurement_file_list(fileId=None))

    # 渲染页面
    return render_template('temperature_details.html',

                           temperature_time_dc1_legend=selected_columns_dc1,
                           temperature_time_tc1_legend=selected_columns_tc1,
                           temperature_time_tc2_legend=selected_columns_tc2,

                           temperature_time_dc1=data_structure_dc1,
                           temperature_time_tc1=data_structure_tc1,
                           temperature_time_tc2=data_structure_tc2,

                           temperature_time_dc1_5=temperature_time_dc1,
                           temperature_time_tc1_6=temperature_time_tc1,
                           temperature_time_tc2_7=temperature_time_tc2,

                           multi_select_html=multi_select_html,
                           init_selected_files=selected_ids,
                           measurement_source=measurement_source
                           )


# ################################################################数据概述#######################################
@temperature_bp.route('/overview', methods=['GET'])
def temperature_overview():
    # 1.获取测量文件列表（网页上选择一个文件或多个)
    fileId: str = request.args.get('fileId')
    try:
        measurement_file_list = get_measurement_file_list(fileId=fileId)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    selected_ids = []
    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
        filtered_files = [file for file in measurement_file_list if file['id'] in selected_ids]

        statistical_variables_list: list = [file['statistical_variable'] for file in filtered_files if
                                            file['statistical_variable'] is not None]
        statistical_variables_str = statistical_variables_list[0]

        project_type: list[str] = [file['oem'] for file in filtered_files]

        measurement_source = filtered_files[0]['source']

    else:
        selected_ids.append(measurement_file_list[0].get('id'))
        filtered_files = measurement_file_list[0]

        statistical_variables_str: str = filtered_files['statistical_variable']
        project_type: list[str] = [filtered_files['oem']]

        measurement_source = filtered_files['source']

    logging.info(f"统计量:{statistical_variables_str}")
    logging.info(f"燃料类型:{measurement_source}")
    logging.info(f"项目:{project_type}")
    logging.info(f"观测文件:{selected_ids}")

    chip_dict_list = chip_dict_in_sql(selected_ids=selected_ids, project_type=project_type)
    logging.info(f"电子元器件字典:{chip_dict_list}")

    # 创建一个字典来存储匹配结果
    statistical_variables_name_list: list[dict] = []
    statistical_variables_list = statistical_variables_str.split(",")
    for variable in statistical_variables_list:
        variable = variable.strip()
        matched_chip = next((chip for chip in chip_dict_list if chip['chip_name'] == variable), None)
        if matched_chip:
            statistical_variables_name_list.append(
                {'measured_variable': matched_chip['measured_variable'], 'chip_name': matched_chip['chip_name']})
        else:
            statistical_variables_name_list.append({'measured_variable': variable, 'chip_name': variable})

    grouped_variables = defaultdict(set)
    for item in statistical_variables_name_list:
        chip_name = item['chip_name']
        measured_variable = item['measured_variable']
        grouped_variables[chip_name].add(measured_variable)
    # 将集合转换为列表
    grouped_variables_list: list = {chip: list(variables) for chip, variables in grouped_variables.items()}
    logging.info(f"统计量(名称:变量):{grouped_variables_list}")

    # 温度时长柱形图和饼状图
    """
        {
            'combined_time_diffs_tecut_dict': combined_time_diffs_tecut_dict,
            'combined_time_diffs_x3_dict': combined_time_diffs_x3_dict,
            'combined_time_diffs_x2_dict': combined_time_diffs_x2_dict,
            'total_minutes_tecut_f': total_minutes_tecut_f,
            'total_minutes_x3_f': total_minutes_x3_f,
            'total_minutes_x2_f': total_minutes_x2_f
       }
        time_diffs_tecut, total_minutes_tecut, time_diffs_tc1th9, total_minutes_tc1th9 
    """
    temperature_duration_dict: dict = temperature_duration(
        file_ids_int=selected_ids,
        max_workers=len(selected_ids), statistical_variables_dict=grouped_variables_list)

    # 温度阈值 和 相对温差
    chip_dict_list = relative_difference(selected_ids, chip_dict_list)
    chip_names = [chip['chip_name'] for chip in chip_dict_list]
    max_allowed_values = [chip['max_allowed_value'] for chip in chip_dict_list]
    max_temperature = [chip['max_temperature'] for chip in chip_dict_list]
    relative_difference_temperature = [-chip['relative_difference_temperature'] for chip in chip_dict_list]

    # 下拉多选框
    multi_select_html = generate_select_options(get_measurement_file_list(fileId=None))

    # 渲染页面
    return render_template('temperature_overview.html',
                           total_minutes_tecut=temperature_duration_dict.get("total_minutes_tecut_f"),
                           total_minutes_x3=temperature_duration_dict.get("total_minutes_x3_f"),
                           total_minutes_x2=temperature_duration_dict.get("total_minutes_x2_f"),

                           time_diffs_tecut=temperature_duration_dict.get("combined_time_diffs_tecut_dict"),
                           time_diffs_x3=temperature_duration_dict.get("combined_time_diffs_x3_dict"),
                           time_diffs_x2=temperature_duration_dict.get("combined_time_diffs_x2_dict"),

                           multi_select_html=multi_select_html,
                           init_selected_files=fileId,

                           chip_names=chip_names,
                           max_allowed_values=max_allowed_values,
                           max_temperature=max_temperature,
                           relative_difference_temperature=relative_difference_temperature,
                           measurement_source=measurement_source
                           )


# #############################################################内部方法不参与解包和封包#######################################
# 获取客户端IP地址
def getClientIp():
    if 'X-Forwarded-For' in request.headers:
        x_forwarded_for = request.headers['X-Forwarded-For']
        # 分割并获取最后一个IP地址
        client_ips = x_forwarded_for.split(',')
        client_ip = client_ips[-1].strip()
    else:
        # 如果没有 X-Forwarded-For 头部，则直接使用远程地址
        client_ip = request.remote_addr
    client_ip = client_ip.replace('.', '')
    logging.info(f"client_ip:{client_ip}")
    return client_ip


def merge(file_name, total_chunks, save_path) -> str:
    save_file = os.path.join(save_path, file_name)

    # 检查所有分片文件是否存在
    temp_files = [os.path.join(save_path, f'{file_name}.part{i}') for i in range(total_chunks)]
    for temp_file in temp_files:
        if not os.path.exists(temp_file):
            raise FileNotFoundError(f'Missing chunk file: {temp_file}')

    # 合并文件
    with open(save_file, 'wb') as outfile:
        for temp_file in temp_files:
            with open(temp_file, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(temp_file)

    return save_file


'''
测量文件数据入库
'''


def get_rename_mapping(columns: list[str]):
    logging.debug(f"get_rename_mapping:{columns}")

    rename_mapping: dict = {}
    for col in columns:
        if '\\' in col:  # TECU_tRaw\ETKC:1
            alias = col.split('\\')[0]
            rename_mapping[col] = alias
        elif re.match(r'.*_ECU\d+', col):  # 匹配包含 _ECU 后跟数字的列名
            parts = col.split('_')
            new_col = '_'.join(parts[:2])  # 只取前两部分
            rename_mapping[col] = new_col
        else:
            rename_mapping[col] = col  # 保持原样

    # 特殊情况处理：TECU_tRaw 列，别名为 TECU_t
    if 'TECU_t' not in columns and 'TECU_tRaw' in columns:
        rename_mapping['TECU_tRaw'] = 'TECU_t'
    return rename_mapping


# 定义一个函数来处理列名
def rename_columns(column_name):
    if '\\' in column_name:
        return column_name.split('\\')[0]
    else:
        return column_name


def sort_and_convert(data):
    """排序并转换数据结构，添加索引"""
    sorted_data = dict(sorted(data.items(), key=lambda item: float(item[0].split(' ~ ')[0])))
    return [
        {**{key: value}, 'idx': idx}
        for idx, (key, value) in enumerate(sorted_data.items())
    ]
