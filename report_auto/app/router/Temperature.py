__coding__ = "utf-8"

import logging
import os

from asammdf import MDF
from asammdf.blocks.utils import MdfException
from flask import request, render_template, jsonify

from app import main
from app.router import temperature_bp
from tools.temperature.temperature_work_time import temperature_duration, temperature_chip, create_data_structure, \
    str_to_list, relative_difference
from tools.utils.DBOperator import create_table, batch_insert_data, insert_data, query_table, delete_from_tables
from tools.utils.DateUtils import getCurDateTime
from tools.utils.FileUtils import get_filename_without_extension
from tools.utils.HtmlGenerator import generate_select_options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

'''
测量文件列表
'''


@temperature_bp.route('/list', methods=['GET'])
def temperature_list():
    table_name = 'measurement_file'
    columns = 'id,file_name'
    whereClause = ' where status = "0" order by id desc'

    try:
        measurement_file_list = query_table(table_name, columns, where=whereClause)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')
    return render_template('temperature_uploader.html', measurement_file_list=measurement_file_list)


'''
测量文件分片上传
'''


@temperature_bp.route('/upload', methods=['POST'])
def temperature_uploader_upload():
    upload_file = request.files['file']

    task_id = request.form.get('task_id')  # 获取文件唯一标识符
    chunk = request.form.get('chunk', 0, type=int)  # 获取该分片在所有分片中的序号
    total_chunks = request.form.get('total_chunks', 1, type=int)  # 获取总分片数
    filename = f'{task_id}_{chunk}'  # 构成该分片唯一标识符
    # print(f"Task: {task_id}, Chunk: {chunk}/{total_chunks}, Filename: {filename}")

    test_team = request.form.get('test_team')
    input_path = main.config['input_path']
    input_path = os.path.join(input_path, test_team)
    input_path = os.path.join(input_path, task_id)
    if not os.path.exists(input_path):
        os.makedirs(input_path, exist_ok=True)

    output_file = os.path.join(input_path, filename)
    upload_file.save(output_file)  # 保存分片到本地
    return {'status': 'success', 'currentChunk': chunk, 'totalChunks': total_chunks, 'task_id': task_id}


'''
测量文件分片合并
'''


@temperature_bp.route('/merge', methods=['POST'])
def temperature_uploader_merge():
    # 获取请求体中的 JSON 数据
    data = request.get_json()
    test_team = data['test_team']
    target_filename = data['filename']
    task_id = data['task_id']  # 获取文件的唯一标识符

    # 最终存储路径
    input_path = main.config['input_path']
    input_path = os.path.join(input_path, test_team)
    if not os.path.exists(input_path):
        os.makedirs(input_path, exist_ok=True)

    # 最终存储文件(带路径)
    target_filename = os.path.join(input_path, target_filename)
    logging.info(f"目标文件路径: {target_filename}")

    chunk = 0  # 分片序号
    with open(target_filename, 'wb') as target_file:  # 创建新文件
        while True:
            try:
                filename = os.path.join(input_path, task_id, f'{task_id}_{chunk}')
                with open(filename, 'rb') as source_file:  # 按序打开每个分片
                    target_file.write(source_file.read())  # 读取分片内容写入新文件
            except IOError:
                break
            chunk += 1
            os.remove(filename)  # 删除该分片，节约空间
    os.removedirs(os.path.join(input_path, task_id))

    into_db = measure_file_intodb(target_filename)
    return into_db


'''
测量文件数据入库
'''


def measure_file_intodb(measure_file_path: str):
    fileName = get_filename_without_extension(measure_file_path)
    table_name = 'measurement_file'
    params: dict = {"file_name": fileName, "create_time": getCurDateTime()}

    # 保存测量文件元信息
    ret_msg, last_id = insert_data(table_name, params)
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
    c_ret_msg = create_table(table_name, df)
    logging.info(c_ret_msg)
    if c_ret_msg != 'success':
        return jsonify({'generate_report_failed': {c_ret_msg}})

    # 批量插入表
    i_ret_msg = batch_insert_data(table_name, df, params)
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

    temperature_time_dc1 = temperature_chip(selected_columns_dc1_str, selected_ids)
    data_structure_dc1 = create_data_structure(temperature_time_dc1, selected_columns_dc1, num_processes=3)

    # #TC1_Th
    selected_columns_tc1_str = "TC1_Th1,TC1_Th2,TC1_Th3,TC1_Th4,TC1_Th5,TC1_Th6,TC1_Th7,TC1_Th8,TC1_Th9,TC1_Th10,TC1_Th11,TC1_Th12,TC1_Th13,TC1_Th14,TC1_Th15,TC1_Th16,TECU_t,timestamps"
    selected_columns_tc1: list = str_to_list(selected_columns_tc1_str)

    temperature_time_tc1 = temperature_chip(selected_columns_tc1_str, selected_ids)
    data_structure_tc1 = create_data_structure(temperature_time_tc1, selected_columns_tc1, num_processes=3)

    # #TC2_Th
    selected_columns_tc2_str: str = "TC2_Th1,TC2_Th2,TC2_Th3,TC2_Th4,TC2_Th5,TC2_Th6,TC2_Th7,TC2_Th8,TC2_Th9,TC2_Th10,TC2_Th11,TC2_Th12,TC2_Th13,TECU_t,timestamps"
    selected_columns_tc2: list = str_to_list(selected_columns_tc2_str)

    temperature_time_tc2 = temperature_chip(selected_columns_tc2_str, selected_ids)
    data_structure_tc2 = create_data_structure(temperature_time_tc2, selected_columns_tc2, num_processes=3)

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
    time_diffs, total_minutes = temperature_duration(selected_ids, max_workers=3)
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
    chip_dict_list = relative_difference(selected_ids)
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

        result, message = delete_from_tables(primary_table_name, second_table_name, primary_param, second_param)

        if result:
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'message': '文件删除失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@temperature_bp.route('/test', methods=['GET'])
def test():
    chip_dict_list = relative_difference()
    # 提取所有chip_name
    chip_names = [chip['chip_name'] for chip in chip_dict_list]
    max_allowed_values = [chip['max_allowed_value'] for chip in chip_dict_list]
    difference_temperatures = [chip['difference_temperature'] for chip in chip_dict_list]
    return render_template('test.html', chip_names=chip_names, max_allowed_values=max_allowed_values,
                           difference_temperatures=difference_temperatures)


'''
获取已上传全部文件元数据
'''


def get_measurement_file_list():
    table_name = 'measurement_file'
    columns = ' file_name,id '
    where = ' where status = "0" order by id desc'

    measurement_file_list = query_table(table_name, columns, where)
    return measurement_file_list


# 定义排序依据
def get_key(item):
    start_time: str = item.split('~')[0]  # 分割时间区间，获取起始时间
    start_time: str = start_time.strip()
    return int(start_time)  # 转换为整数以便排序
