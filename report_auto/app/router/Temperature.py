__coding__ = "utf-8"

import logging
import os
import time

from asammdf import MDF
from asammdf.blocks.utils import MdfException
from flask import request, render_template, jsonify

from app import main, db_pool
from app.router import temperature_bp
from tools.temperature.temperature_work_time import str_to_list, relative_difference
from tools.temperature.temperature_work_time import temperature_duration, temperature_chip, create_data_structure
from tools.utils.DBOperator import create_table, batch_insert_data, insert_data, query_table, delete_from_tables
from tools.utils.DateUtils import getCurDateTime
from tools.utils.FileUtils import extract_prefix
from tools.utils.HtmlGenerator import generate_select_options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def monitor_pool_status(interval=10):
    """
    定期监控连接池状态
    :param interval: 监控间隔时间（秒）
    """
    while True:
        status = db_pool.get_pool_status()
        logging.info("Database pool status: %s", status)
        time.sleep(interval)


@temperature_bp.route('/', methods=['GET'])
def temperature_idx():
    return render_template('temperature.html')


'''
测量文件列表
'''


@temperature_bp.route('/list', methods=['GET'])
def temperature_list():
    try:
        measurement_file_list = get_measurement_file_list()
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

    file = request.files['file']
    chunk_index = int(request.form.get('chunk', 0))
    total_chunks = int(request.form.get('chunks', 1))
    file_name = request.form.get('name')

    input_path = main.config['input_path']
    test_team = request.form.get('test_team')
    input_path = os.path.join(input_path, test_team)
    input_path = os.path.join(input_path, client_ip)
    if not os.path.exists(input_path):
        os.makedirs(input_path, exist_ok=True)

    save_file = ''
    msg = ''
    try:
        temp_file_path = os.path.join(input_path, f'{file_name}.part{chunk_index}')
        file.save(temp_file_path)  # 存储分片

        if chunk_index == total_chunks - 1:
            save_file = merge(file_name, total_chunks)  # 分片合并
    except Exception as e:
        msg = f'{e}'
        logging.error(f'file saved err:{msg}')

    return {'status': 'success', 'save_file': save_file, 'msg': msg}


def merge(file_name, total_chunks) -> str:
    client_ip = getClientIp()

    save_path = main.config['input_path']
    test_team = request.form.get('test_team')
    save_path = os.path.join(save_path, test_team)
    save_path = os.path.join(save_path, client_ip)

    if not os.path.exists(save_path):
        os.makedirs(save_path, exist_ok=True)

    save_file = os.path.join(save_path, file_name)
    temp_files = [os.path.join(save_path, f'{file_name}.part{i}') for i in range(total_chunks)]
    with open(save_file, 'wb') as outfile:
        for temp_file in temp_files:
            with open(temp_file, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(temp_file)
    return save_file


'''
测量文件数据入库
'''


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

    mdf = MDF(measure_file_path)
    selected_columns = ['DC1_Th1', 'DC1_Th2', 'DC1_Th3', 'DC1_Th4', 'DC1_Th5', 'DC1_Th6', 'DC1_Th7',
                        'DC1_Th8', 'TC1_Th1', 'TC1_Th2', 'TC1_Th3', 'TC1_Th4', 'TC1_Th5', 'TC1_Th6',
                        'TC1_Th7', 'TC1_Th8', 'TC1_Th9', 'TC1_Th10', 'TC1_Th11', 'TC1_Th12', 'TC1_Th13',
                        'TC1_Th14', 'TC1_Th15', 'TC1_Th16', 'TC2_Th1', 'TC2_Th2', 'TC2_Th3', 'TC2_Th4',
                        'TC2_Th5', 'TC2_Th6', 'TC2_Th7', 'TC2_Th8', 'TC2_Th9', 'TC2_Th10', 'TC2_Th11',
                        'TC2_Th12', 'TC2_Th13']
    # 检查并添加 TECU_tRaw 或 TECU_t 列
    if 'TECU_tRaw' in mdf:
        selected_columns.append('TECU_tRaw')
        alias_column = 'TECU_tRaw'
    elif 'TECU_t' in mdf:
        selected_columns.append('TECU_t')
        alias_column = 'TECU_t'
    else:
        alias_column = None

    # 过滤掉不存在的列
    existing_columns = [col for col in selected_columns if col in mdf.channels_db]
    try:
        df = mdf.to_dataframe(channels=existing_columns)
    except MdfException as e:
        logging.error(f"Error converting to DataFrame: {e}")
        return jsonify({'generate_report_failed': {e}})

    # TECU_tRaw\ETKC:1
    column_names = df.columns.tolist()
    alias_column_names = {item: item.split('\\')[0] for item in column_names}
    df.rename(columns=alias_column_names, inplace=True)

    # 如果存在 TECU_tRaw 或 TECU_t 列，为其起别名
    if alias_column is not None:
        df.rename(columns={alias_column: 'TECU_t'}, inplace=True)

    # 去除连续的重复行
    # 首先对 DataFrame 进行排序，确保按时间顺序排列
    df.sort_values(by='timestamps', inplace=True)
    logging.info(f"排序:{len(df)}")

    # 使用 keep='first' 选项保留第一次出现的非重复行
    df.drop_duplicates(keep='first', inplace=True)
    logging.info(f"删除重复项:{len(df)}")

    df.reset_index(inplace=True)
    logging.info(f"重置索引:{len(df)}")

    table_name = 'chip_temperature'
    params: dict = {'file_id': last_id}

    # 创建表
    c_ret_msg = create_table(db_pool, table_name=table_name, df=df)
    logging.info(c_ret_msg)
    if c_ret_msg != 'success':
        return jsonify({'generate_report_failed': {c_ret_msg}})

    # 批量插入表
    i_ret_msg = batch_insert_data(db_pool, table_name=table_name, params=params, df=df)
    logging.info(i_ret_msg)
    if i_ret_msg != 'success':
        return jsonify({'generate_report_failed': {i_ret_msg}})

    return jsonify({'generate_report_failed': ''})


'''
数据详情
'''


@temperature_bp.route('/details', methods=['GET'])
def temperature_details():
    # 获取已上传文件的元数据
    measurement_file_list = None
    selected_ids = []
    try:
        measurement_file_list = get_measurement_file_list()
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    # 请求报文中获取请求参数fileId
    fileId = request.args.get('fileId')
    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
    else:
        selected_ids.append(measurement_file_list[0].get('id'))

    # 折线图
    # #DC1_Th
    selected_columns_dc1_str = 'DC1_Th1,DC1_Th2,DC1_Th3,DC1_Th4,DC1_Th5,DC1_Th6,DC1_Th7,DC1_Th8,TECU_t,timestamps'
    selected_columns_dc1: list = str_to_list(selected_columns_dc1_str)

    temperature_time_dc1 = temperature_chip(db_pool, selected_columns=selected_columns_dc1_str,
                                            file_ids_int=selected_ids)
    data_structure_dc1 = create_data_structure(temperature_time_dc1, selected_columns_dc1, num_processes=2)

    # #TC1_Th
    selected_columns_tc1_str = "TC1_Th1,TC1_Th2,TC1_Th3,TC1_Th4,TC1_Th5,TC1_Th6,TC1_Th7,TC1_Th8,TC1_Th9,TC1_Th10,TC1_Th11,TC1_Th12,TC1_Th13,TC1_Th14,TC1_Th15,TC1_Th16,TECU_t,timestamps"
    selected_columns_tc1: list = str_to_list(selected_columns_tc1_str)

    temperature_time_tc1 = temperature_chip(db_pool, selected_columns=selected_columns_tc1_str,
                                            file_ids_int=selected_ids)
    data_structure_tc1 = create_data_structure(temperature_time_tc1, selected_columns_tc1, num_processes=2)

    # #TC2_Th
    selected_columns_tc2_str: str = "TC2_Th1,TC2_Th2,TC2_Th3,TC2_Th4,TC2_Th5,TC2_Th6,TC2_Th7,TC2_Th8,TC2_Th9,TC2_Th10,TC2_Th11,TC2_Th12,TC2_Th13,TECU_t,timestamps"
    selected_columns_tc2: list = str_to_list(selected_columns_tc2_str)

    temperature_time_tc2 = temperature_chip(db_pool, selected_columns=selected_columns_tc2_str,
                                            file_ids_int=selected_ids)
    data_structure_tc2 = create_data_structure(temperature_time_tc2, selected_columns_tc2, num_processes=2)

    # 下拉复选框
    multi_select_html = generate_select_options(measurement_file_list)

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
                           init_selected_files=selected_ids
                           )


'''
数据概述
'''


@temperature_bp.route('/overview', methods=['GET'])
def temperature_overview():
    # 获取所有上传文件的元数据
    selected_ids = []
    try:
        measurement_file_list = get_measurement_file_list()
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    # 请求报文中获取参数fileId
    fileId = request.args.get('fileId')
    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
    else:
        selected_ids.append(measurement_file_list[0].get('id'))

    # 温度时长柱形图和饼状图
    time_diffs, total_minutes = temperature_duration(db_pool, file_ids_int=selected_ids, max_workers=2)
    # 使用排序函数
    sorted_data = dict(sorted(time_diffs.items(), key=lambda item: float(item[0].split(' ~ ')[0])))
    # 创建转换后的数据结构，并添加索引
    time_diffs = [
        {**{key: value}, 'idx': idx}
        for idx, (key, value) in enumerate(sorted_data.items())
    ]
    # 下拉多选框
    multi_select_html = generate_select_options(measurement_file_list)

    # 温度阈值 和 相对温差
    chip_dict_list = relative_difference(db_pool, selected_ids)
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

        result, message = delete_from_tables(db_pool, primary_table_name=primary_table_name,
                                             primary_param=primary_param)
        if result:
            result, message = delete_from_tables(db_pool, second_table_name=second_table_name,
                                                 second_param=second_param)
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


def get_measurement_file_list():
    query_sql = 'SELECT file_name, id FROM measurement_file WHERE status = %s ORDER BY id DESC'
    params = ('0',)
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)
    return measurement_file_list


# 定义排序依据
def get_key(item):
    start_time: str = item.split('~')[0]  # 分割时间区间，获取起始时间
    start_time: str = start_time.strip()
    return int(start_time)  # 转换为整数以便排序
