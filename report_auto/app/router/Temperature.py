__coding__ = "utf-8"

import logging
import os
import re
import time
from typing import Dict, List

from asammdf import MDF
from asammdf.blocks.utils import MdfException
from flask import request, render_template, jsonify
from werkzeug.utils import secure_filename

from app import db_pool, env_input_path
from app.router import temperature_bp
from tools.temperature.temperature_work_time import relative_difference, chip_dict
from tools.temperature.temperature_work_time import temperature_duration, temperature_chip, create_data_structure
from tools.utils.DBOperator import create_table, batch_insert_data, insert_data, query_table, delete_from_tables, \
    update_table, alter_table_add_columns
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
        measurement_file_list = get_measurement_file_list(fileId=None)
    except Exception as e:
        logging.error(f'查询异常:{e}')
        return render_template('error.html', failure_msg=f'{e}')
    return render_template('temperature_uploader.html', measurement_file_list=measurement_file_list)


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

    source: str = 'v1'
    rename_mapping: dict = {}
    for col in columns:
        if '\\' in col:  # TECU_tRaw\ETKC:1
            alias = col.split('\\')[0]
            rename_mapping[col] = alias
        elif re.match(r'.*_ECU\d+', col):  # 匹配包含 _ECU 后跟数字的列名
            parts = col.split('_')
            new_col = '_'.join(parts[:2])  # 只取前两部分
            rename_mapping[col] = new_col
            source = 'v2'
        else:
            rename_mapping[col] = col  # 保持原样

    # 特殊情况处理：TECU_tRaw 列，别名为 TECU_t
    if 'TECU_t' not in columns and 'TECU_tRaw' in columns:
        rename_mapping['TECU_tRaw'] = 'TECU_t'
    return source, rename_mapping


@temperature_bp.route('/todb', methods=['POST'])
def todb():
    data = request.get_json()
    measure_file_path = data['save_file']
    logging.info(f"measure_file_path:{measure_file_path}")

    fileName = extract_prefix(measure_file_path)
    table_name = 'measurement_file'
    params: dict = {"file_name": fileName, "create_time": getCurDateTime()}

    # 保存测量文件元信息
    ret_msg, last_id = insert_data(db_pool, table_name=table_name, params=params)
    if ret_msg != 'success':
        return jsonify({'generate_report_failed': ret_msg})
    logging.info(f"文件元信息索引:{last_id}")

    # 1.采集测量数据
    mdf = MDF(measure_file_path)
    query = "select value from tool_parameters where name =%s  and status =%s "
    params = ('HTM_SELECTED_COLUMNS', 'active')

    selected_columns_dict: list[dict] = query_table(db_pool, query=query, params=params)
    selected_columns_str = selected_columns_dict[0].get("value")
    selected_columns = [col.strip("' ") for col in selected_columns_str.strip("[]").split(",")]
    logging.info(f"[信号列]已配置:{selected_columns}")

    channels_db_keys = mdf.channels_db.keys()
    logging.debug(f"[信号列]本次采集:{channels_db_keys}")

    existing_columns = [col for col in selected_columns if col in channels_db_keys]
    logging.debug(f"[信号列]可采集:{existing_columns}")

    try:
        df = mdf.to_dataframe(channels=existing_columns)
    except MdfException as e:
        logging.error(f"Error converting to DataFrame: {e}")
        return jsonify({'generate_report_failed': {e}})

    # 重命名DataFrame中的列
    df.rename(columns={df.columns[0]: rename_columns(df.columns[0])}, inplace=True)
    column_names = df.columns.tolist()

    # 2. 数据清洗
    # 构建列名映射字典
    source, rename_mapping = get_rename_mapping(column_names)
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
    table_name = 'chip_temperature'
    params: dict = {'file_id': last_id, 'source': source}

    # 创建表
    c_ret_msg, columns_in_db = create_table(db_pool, table_name=table_name, df=df)
    if c_ret_msg != 'success':
        return jsonify({'generate_report_failed': {c_ret_msg}})

    # 找出 rename_mapping 中不在 columns_in_db 中的键
    missing_keys = [key for key in rename_mapping if key not in columns_in_db]
    logging.info(f"表{table_name}添加列:{missing_keys}")
    if len(missing_keys) >= 1:
        op_flag, op_msg = alter_table_add_columns(db_pool, table=table_name, columns=missing_keys, column_type="double")
        logging.info(f"{op_flag},{op_msg}")

    # 批量插入表
    i_ret_msg = batch_insert_data(db_pool, table_name=table_name, params=params, df=df)
    if i_ret_msg != 'success':
        return jsonify({'generate_report_failed': {i_ret_msg}})

    # 特殊信号量
    special_columns: list = ['timestamps']
    keys_set = set(rename_mapping.keys())

    if 'v2' == source and 'TC1_Th9' in keys_set:
        special_columns.append('TC1_Th9')
    else:
        if 'TECU_t' in keys_set:
            special_columns.append('TECU_t')
        if 'EnvT_t' in keys_set:
            special_columns.append('EnvT_t')

    special_columns_str = ",".join(special_columns)

    # 测量文件来源
    update_table(db_pool, table='measurement_file',
                 set_params={'source': source, "special_columns": special_columns_str}, where_params={'id': last_id})
    return jsonify({'generate_report_failed': ''})


'''
数据详情
'''


@temperature_bp.route('/details', methods=['GET'])
def temperature_details():
    selected_ids = []
    # 获取已上传文件的元数据
    measurement_file_list = None
    # v1版本
    measurement_source = 'v1'
    # 请求报文中获取请求参数fileId
    fileId = request.args.get('fileId')

    try:
        measurement_file_list = get_measurement_file_list(fileId)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
    else:
        selected_ids.append(measurement_file_list[0].get('id'))
    measurement_source = measurement_file_list[0].get('source')

    # 折线图
    r_chip_dict: list[dict] = chip_dict(measurement_source=measurement_source)
    kv_chip_dict: dict = {item['measured_variable']: item['chip_name'] for item in r_chip_dict}
    logging.info(f"芯片字典:{r_chip_dict}")

    # 提取所有的 measured_variable
    measured_variables_list: list[str] = [item['measured_variable'] for item in r_chip_dict]
    logging.info(f"芯片字典-信号量:{measured_variables_list}")

    # 使用集合推导式提取并合并所有 special_columns
    all_special_columns = set(
        column for file_info in measurement_file_list for column in file_info.get('special_columns', '').split(','))
    # 将集合转换为列表
    all_special_columns_list = list(all_special_columns)
    logging.info(f"特殊信号量:{all_special_columns_list}")

    # #DC1_Th
    selected_columns_dc1: list = []
    temperature_time_dc1: Dict[str, List] = {}
    data_structure_dc1: list = []
    dc1_measured_variables_list = [var for var in measured_variables_list if var.startswith('DC1_')]
    if len(dc1_measured_variables_list) > 0:
        dc1_measured_variables_list.extend(all_special_columns_list)
        if 'v2' == measurement_source:
            dc1_measured_variables_list.append('TC1_Th9')
        logging.info(f"DC1_组件信号量:{dc1_measured_variables_list}")

        filtered_chips = [chip for chip in r_chip_dict if chip['measured_variable'] in dc1_measured_variables_list]
        selected_columns_dc1 = [chip['chip_name'] for chip in filtered_chips]  # 提取芯片名称
        logging.info(f"DC1_组件信号量中文名:{selected_columns_dc1}")

        selected_columns_dc1_str = ','.join(dc1_measured_variables_list)
        temperature_time_dc1 = temperature_chip(selected_columns=selected_columns_dc1_str,
                                                file_ids_int=selected_ids, measurement_source=measurement_source,
                                                kv_chip_dict=kv_chip_dict)
        data_structure_dc1 = create_data_structure(temperature_time_dc1, selected_columns_dc1, measurement_source,
                                                   num_processes=len(selected_ids))

    # #TC1_Th
    selected_columns_tc1: list = []
    temperature_time_tc1: Dict[str, List] = {}
    data_structure_tc1: list = []
    tc1_measured_variables_list = [var for var in measured_variables_list if var.startswith('TC1_')]
    if len(tc1_measured_variables_list) > 0:
        tc1_measured_variables_list.extend(all_special_columns_list)
        logging.info(f"TC1_组件信号量:{tc1_measured_variables_list}")

        filtered_chips = [chip for chip in r_chip_dict if chip['measured_variable'] in tc1_measured_variables_list]
        selected_columns_tc1 = [chip['chip_name'] for chip in filtered_chips]  # 提取芯片名称
        logging.info(f"TC1_组件信号量中文名:{selected_columns_tc1}")

        selected_columns_tc1_str = ','.join(tc1_measured_variables_list)
        temperature_time_tc1 = temperature_chip(selected_columns=selected_columns_tc1_str,
                                                file_ids_int=selected_ids, measurement_source=measurement_source,
                                                kv_chip_dict=kv_chip_dict)
        data_structure_tc1 = create_data_structure(temperature_time_tc1, selected_columns_tc1, measurement_source,
                                                   num_processes=len(selected_ids))

    # #TC2_Th
    selected_columns_tc2: list = []
    temperature_time_tc2: Dict[str, List] = {}
    data_structure_tc2: list = []
    tc2_measured_variables_list = [var for var in measured_variables_list if var.startswith('TC2_')]
    if len(tc2_measured_variables_list) > 0:
        tc2_measured_variables_list.extend(all_special_columns_list)
        if 'v2' == measurement_source:
            tc2_measured_variables_list.append('TC1_Th9')
        logging.info(f"TC2_组件信号量:{tc2_measured_variables_list}")

        # 过滤 r_chip_dict 中与 tc2_measured_variables_list 匹配的项
        filtered_chips = [chip for chip in r_chip_dict if chip['measured_variable'] in tc2_measured_variables_list]
        selected_columns_tc2 = [chip['chip_name'] for chip in filtered_chips]  # 提取芯片名称
        logging.info(f"TC2_组件信号量中文名:{selected_columns_tc2}")

        selected_columns_tc2_str = ','.join(tc2_measured_variables_list)
        temperature_time_tc2 = temperature_chip(selected_columns=selected_columns_tc2_str,
                                                file_ids_int=selected_ids, measurement_source=measurement_source,
                                                kv_chip_dict=kv_chip_dict)

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
    # 获取所有上传文件的元数据
    selected_ids = []
    # 请求报文中获取参数fileId
    fileId: str = request.args.get('fileId')
    measurement_source: str = 'v1'
    try:
        measurement_file_list = get_measurement_file_list(fileId)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
    else:
        selected_ids.append(measurement_file_list[0].get('id'))

    measurement_source = measurement_file_list[0].get('source')
    logging.info(f"测量文件来源:{measurement_source}")

    # 使用集合推导式提取并合并所有 special_columns
    all_special_columns = set(
        column for file_info in measurement_file_list for column in file_info.get('special_columns', '').split(','))
    # 将集合转换为列表
    all_special_columns_list = list(all_special_columns)
    all_special_columns_str = ",".join(all_special_columns_list)
    logging.info(f"特殊信号量:{all_special_columns_str}")

    # 温度时长柱形图和饼状图
    time_diffs, total_minutes = temperature_duration(db_pool, file_ids_int=selected_ids, max_workers=len(selected_ids),
                                                     measurement_source=measurement_source,
                                                     all_special_columns_str=all_special_columns_str)
    # 使用排序函数
    sorted_data = dict(sorted(time_diffs.items(), key=lambda item: float(item[0].split(' ~ ')[0])))
    # 创建转换后的数据结构，并添加索引
    time_diffs = [
        {**{key: value}, 'idx': idx}
        for idx, (key, value) in enumerate(sorted_data.items())
    ]
    # 下拉多选框
    multi_select_html = generate_select_options(get_measurement_file_list(fileId=None))

    # 温度阈值 和 相对温差
    chip_dict_list = relative_difference(db_pool, selected_ids, measurement_source=measurement_source)
    chip_names = [chip['chip_name'] for chip in chip_dict_list]
    max_allowed_values = [chip['max_allowed_value'] for chip in chip_dict_list]
    max_temperature = [chip['max_temperature'] for chip in chip_dict_list]
    relative_difference_temperature = [-chip['relative_difference_temperature'] for chip in chip_dict_list]

    # 渲染页面
    return render_template('temperature_overview.html',
                           total_minutes=total_minutes,
                           time_diffs=time_diffs,

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


def get_measurement_file_list(fileId: str):
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


# 定义排序依据
def get_key(item):
    start_time: str = item.split('~')[0]  # 分割时间区间，获取起始时间
    start_time: str = start_time.strip()
    return int(start_time)  # 转换为整数以便排序


# 定义一个函数来处理列名
def rename_columns(column_name):
    if '\\' in column_name:
        return column_name.split('\\')[0]
    else:
        return column_name
