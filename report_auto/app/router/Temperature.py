__coding__ = "utf-8"

import logging
import os
import re
import time
from typing import Dict, List

from asammdf import MDF
from asammdf.blocks.utils import MdfException
from flask import request, jsonify, render_template
from pandas import DataFrame
from werkzeug.utils import secure_filename

from app import db_pool, env_input_path
from app.router import temperature_bp
from tools.temperature.temperature_work_time import relative_difference, chip_dict
from tools.temperature.temperature_work_time import temperature_duration, temperature_chip, create_data_structure
from tools.utils.DBOperator import create_table, batch_insert_data, insert_data, query_table, delete_from_tables, \
    alter_table_add_columns, update_table
from tools.utils.DateUtils import getCurDateTime
from tools.utils.FileUtils import extract_prefix
from tools.utils.HtmlGenerator import generate_select_options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@temperature_bp.route('/db_status', methods=['GET'])
def monitor_pool_status(interval=10):
    """
    定期监控连接池状态
    :param interval: 监控间隔时间（秒）
    """
    while True:
        status = db_pool.get_pool_status()
        logging.info("Database pool status: %s", status)
        time.sleep(interval)
    return {'status': status}


@temperature_bp.route('/', methods=['GET'])
def temperature_idx():
    return render_template('temperature.html')


'''
测量文件列表
'''


@temperature_bp.route('/list', methods=['GET'])
def temperature_list():
    try:
        measurement_file_source_list = get_measurement_file_source_list()
    except Exception as e:
        logging.error(f'查询异常:{e}')
        return render_template('error.html', failure_msg=f'{e}')
    return render_template('temperature_uploader.html',
                           measurement_file_source_list=measurement_file_source_list)


@temperature_bp.route('/list/page', methods=['GET'])
def temperature_list_page():
    try:
        # 获取分页参数
        pageNum = int(request.args.get('pageNum', 1))  # 默认值为 1
        pageSize = int(request.args.get('pageSize', 10))  # 默认值为 10

        # 计算数据库查询的起始位置和结束位置
        start = (pageNum - 1) * pageSize
        end = start + pageSize

        # 调用函数获取分页数据
        total_count, measurement_file_list = get_measurement_file_list_page(start=start, end=end)

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


def getClientIp():
    client_ip = ''
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


@temperature_bp.route('/upload', methods=['POST'])
def upload():
    client_ip = getClientIp()
    # 获取上传文件和相关参数
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

    return jsonify({'status': 'success', 'save_file': save_file, 'msg': msg})


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


@temperature_bp.route('/todb', methods=['POST'])
def todb():
    data = request.get_json()
    file_source = data['file_source']
    measure_file_path = data['save_file']
    logging.info(f"measure_file_path:{measure_file_path}")

    fileName = extract_prefix(measure_file_path)
    table_name = 'measurement_file'
    params: dict = {"file_name": fileName, "create_time": getCurDateTime(), 'source': file_source}

    # 保存测量文件元信息
    ret_msg, last_id = insert_data(db_pool, table_name=table_name, params=params)
    if ret_msg != 'success':
        return jsonify({'generate_report_failed': ret_msg})
    logging.info(f"文件元信息索引:{last_id}")

    # 1.采集测量数据
    mdf = MDF(measure_file_path)
    query = "select value from tool_parameters where name =%s  and status =%s "
    params = (file_source, 'active')

    selected_columns_dict: list[dict] = query_table(db_pool, query=query, params=params)
    selected_columns_str = selected_columns_dict[0].get("value")
    selected_columns = [col.strip("' ") for col in selected_columns_str.strip("[]").split(",")]
    logging.info(f"[信号量]已配置:{selected_columns}")

    channels_db_keys = mdf.channels_db.keys()
    logging.info(f"[信号量]待采集:{channels_db_keys}")

    existing_columns = list(set(col for col in selected_columns if col in channels_db_keys))
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

    # df.reset_index(inplace=True)
    # logging.info(f"重置索引:{len(df)}")

    # 3.数据保存

    # 更新measurement_file，特殊列
    params: dict = {}
    if 'DS_FILES' == file_source:
        params['special_columns'] = 'timestamps,TECU_t'
    elif 'NG_FILES' == file_source:
        ng_files_str: str = 'timestamps,TC1_Th9'
        if 'TECU_t' in rename_mapping:
            ng_files_str = ','.join([ng_files_str, 'TECU_t'])  # 使用 join 方法将新列名添加到字符串中
        params['special_columns'] = ng_files_str
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


'''
数据详情
'''


@temperature_bp.route('/details', methods=['GET'])
def temperature_details():
    selected_ids = []
    measurement_file_list = None
    measurement_source = ''
    fileId = request.args.get('fileId')

    # 1. 获取测量文件列表
    try:
        measurement_file_list = get_measurement_file_list(fileId=fileId)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    all_special_columns_list: list = []
    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
        all_special_columns = set(
            column for file_info in measurement_file_list for column in file_info.get('special_columns', '').split(','))
        all_special_columns_list = list(all_special_columns)
    else:
        selected_ids.append(measurement_file_list[0].get('id'))
        all_special_columns_list = [measurement_file_list[0].get('special_columns')]

    measurement_source = measurement_file_list[0].get('source')
    logging.info(f"特殊信号量:{all_special_columns_list},文件来源:{measurement_source}")

    # 2. 获取芯片字典列表
    r_chip_dict: list[dict] = chip_dict(measurement_source=measurement_source)
    kv_chip_dict: dict = {item['measured_variable']: item['chip_name'] for item in r_chip_dict}
    measured_variables_list: list[str] = [item['measured_variable'] for item in r_chip_dict]
    logging.info(f"芯片字典-NG全部信号量:{measured_variables_list}")

    # 折线图
    # #DC1_Th
    selected_columns_dc1: list = []
    temperature_time_dc1: Dict[str, List] = {}
    data_structure_dc1: list = []
    dc1_measured_variables_list = [var for var in measured_variables_list if var.startswith('DC1_')]
    if len(dc1_measured_variables_list) > 0:
        for column in all_special_columns_list:
            dc1_measured_variables_list.extend(column.split(','))
        dc1_measured_variables_list = list(set(dc1_measured_variables_list))
        logging.info(f"DC1_组件信号量:{dc1_measured_variables_list}")

        temperature_time_dc1 = temperature_chip(selected_columns=','.join(dc1_measured_variables_list),
                                                file_ids_int=selected_ids, measurement_source=measurement_source,
                                                kv_chip_dict=kv_chip_dict)

        selected_columns_dc1 = [key for key in temperature_time_dc1 if key != 'timestamps']
        logging.info(f"DC1_组件信号量中文名:{selected_columns_dc1}")

        data_structure_dc1 = create_data_structure(temperature_time_dc1, selected_columns_dc1, measurement_source,
                                                   num_processes=len(selected_ids))

    # #TC1_Th
    selected_columns_tc1: list = []
    temperature_time_tc1: Dict[str, List] = {}
    data_structure_tc1: list = []
    tc1_measured_variables_list = [var for var in measured_variables_list if var.startswith('TC1_')]
    if len(tc1_measured_variables_list) > 0:
        # 将特殊列分解并添加到原始列表中
        for column in all_special_columns_list:
            tc1_measured_variables_list.extend(column.split(','))
        tc1_measured_variables_list = list(set(tc1_measured_variables_list))
        logging.info(f"TC1_组件信号量:{tc1_measured_variables_list}")

        temperature_time_tc1 = temperature_chip(selected_columns=','.join(tc1_measured_variables_list),
                                                file_ids_int=selected_ids, measurement_source=measurement_source,
                                                kv_chip_dict=kv_chip_dict)
        selected_columns_tc1 = [key for key in temperature_time_tc1 if key != 'timestamps']
        logging.info(f"TC1_组件信号量中文名:{selected_columns_tc1}")

        data_structure_tc1 = create_data_structure(temperature_time_tc1, selected_columns_tc1, measurement_source,
                                                   num_processes=len(selected_ids))

    # #TC2_Th
    selected_columns_tc2: list = []
    temperature_time_tc2: Dict[str, List] = {}
    data_structure_tc2: list = []
    tc2_measured_variables_list = [var for var in measured_variables_list if var.startswith('TC2_')]
    if len(tc2_measured_variables_list) > 0:
        for column in all_special_columns_list:
            tc2_measured_variables_list.extend(column.split(','))
        tc2_measured_variables_list = list(set(tc2_measured_variables_list))
        logging.info(f"TC2_组件信号量:{tc2_measured_variables_list}")

        temperature_time_tc2 = temperature_chip(selected_columns=','.join(tc2_measured_variables_list),
                                                file_ids_int=selected_ids, measurement_source=measurement_source,
                                                kv_chip_dict=kv_chip_dict)

        # 过滤 r_chip_dict 中与 tc2_measured_variables_list 匹配的项
        selected_columns_tc2 = [key for key in temperature_time_tc2 if key != 'timestamps']
        logging.info(f"TC2_组件信号量中文名:{selected_columns_tc2}")

        data_structure_tc2 = create_data_structure(temperature_time_tc2, selected_columns_tc2, measurement_source,
                                                   num_processes=len(selected_ids))

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


'''
数据概述
'''


@temperature_bp.route('/overview', methods=['GET'])
def temperature_overview():
    logging.info("数据概览")
    # 获取所有上传文件的元数据
    selected_ids = []
    # 请求报文中获取参数fileId
    fileId: str = request.args.get('fileId')
    measurement_source: str = 'DS_FILES'
    try:
        # 获取测量文件列表
        measurement_file_list = get_measurement_file_list(fileId=fileId)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    all_special_columns_str: str = ''
    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
        # 使用集合推导式提取并合并所有 special_columns
        all_special_columns = set(
            column
            for file_info in measurement_file_list
            for column in file_info.get('special_columns', '').split(',')
        )
        # 将集合转换为列表
        all_special_columns_list = list(all_special_columns)
        all_special_columns_str = ",".join(all_special_columns_list)
        logging.info(f"特殊信号量:{all_special_columns_str}")
    else:
        selected_ids.append(measurement_file_list[0].get('id'))
        all_special_columns_str = measurement_file_list[0].get('special_columns')

    measurement_source = measurement_file_list[0].get('source')
    logging.info(f"测量文件来源:{measurement_source}")

    # 温度时长柱形图和饼状图
    time_diffs_tecut, total_minutes_tecut, time_diffs_tc1th9, total_minutes_tc1th9 = temperature_duration(
        file_ids_int=selected_ids, max_workers=len(selected_ids),
        measurement_source=measurement_source,
        all_special_columns_str=all_special_columns_str)

    # # 排序并转换数据结构，添加索引
    # time_diffs_tecut = sort_and_convert(time_diffs_tecut)
    # time_diffs_tc1th9 = sort_and_convert(time_diffs_tc1th9)

    # 下拉多选框

    multi_select_html = generate_select_options(get_measurement_file_list(fileId=None))

    # 温度阈值 和 相对温差
    chip_dict_list = relative_difference(selected_ids, measurement_source=measurement_source)
    chip_names = [chip['chip_name'] for chip in chip_dict_list]
    max_allowed_values = [chip['max_allowed_value'] for chip in chip_dict_list]
    max_temperature = [chip['max_temperature'] for chip in chip_dict_list]
    relative_difference_temperature = [-chip['relative_difference_temperature'] for chip in chip_dict_list]

    # 渲染页面
    return render_template('temperature_overview.html',
                           total_minutes_tecut=total_minutes_tecut,
                           total_minutes_tc1th9=total_minutes_tc1th9,
                           time_diffs_tecut=time_diffs_tecut,
                           time_diffs_tc1th9=time_diffs_tc1th9,

                           multi_select_html=multi_select_html,
                           init_selected_files=fileId,

                           chip_names=chip_names,
                           max_allowed_values=max_allowed_values,
                           max_temperature=max_temperature,
                           relative_difference_temperature=relative_difference_temperature,
                           measurement_source=measurement_source
                           )


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


'''
获取已上传全部文件元数据
'''


def get_measurement_file_list(fileId: str = None):
    logging.info(">>测量文件列表:")
    # 构建基础查询语句
    query_sql = 'SELECT file_name, id, source,special_columns,source FROM measurement_file WHERE status = %s'

    # 如果提供了 fileId，则添加额外的过滤条件
    params = ['0']  # 初始化参数列表
    if fileId:
        # 将 fileId 字符串分割成列表
        id_list = [int(id.strip()) for id in fileId.split(',')]
        # 添加 IN 子句到查询语句
        query_sql += ' AND id IN ({})'.format(','.join(['%s'] * len(id_list)))
        # 将 id 列表添加到参数列表
        params.extend(id_list)

    # 添加排序子句
    query_sql += ' ORDER BY id DESC'

    # 执行查询
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)
    return measurement_file_list


'''
测量文件列表(分页)
'''


def get_measurement_file_list_page(fileId: str = None, start=None, end=None):
    # 构建基础查询语句
    query_sql = 'SELECT file_name, id, source, special_columns, source,create_time FROM measurement_file WHERE status = %s'

    # 如果提供了 fileId，则添加额外的过滤条件
    params = ['0']  # 初始化参数列表
    if fileId:
        # 将 fileId 字符串分割成列表
        id_list = [int(id.strip()) for id in fileId.split(',')]
        # 添加 IN 子句到查询语句
        query_sql += ' AND id IN ({})'.format(','.join(['%s'] * len(id_list)))
        # 将 id 列表添加到参数列表
        params.extend(id_list)

    # 添加排序子句
    query_sql += ' ORDER BY id DESC'

    # 如果提供了分页参数，则添加 LIMIT 和 OFFSET 子句
    if start is not None and end is not None:
        query_sql += ' LIMIT %s OFFSET %s'
        params.append(end - start)  # 每页数据量
        params.append(start)  # 起始位置

    # 执行查询
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)

    # 计算总记录数
    count_sql = 'SELECT COUNT(*) as total FROM measurement_file WHERE status = %s'
    if fileId:
        count_sql += ' AND id IN ({})'.format(','.join(['%s'] * len(id_list)))
        params_for_count = ['0'] + id_list
    else:
        params_for_count = ['0']

    total_count_df: DataFrame = query_table(db_pool, query=count_sql, params=params_for_count)
    total_count = total_count_df[0].get("total")
    return total_count, measurement_file_list


'''字典表:测量文件来源'''


def get_measurement_file_source_list():
    # 构建基础查询语句
    query_sql = 'select dict_value,dict_name from tool_dictionary where dict_type = %s order by dict_id'
    params = ['file_source']  # 初始化参数列表
    # 执行查询
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)
    return measurement_file_list


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
