__coding__ = "utf-8"

import logging
import os

from flask import request, jsonify, render_template
from werkzeug.utils import secure_filename

from app import db_pool, env_input_path
from app.router import temperature_bp
from app.router.Temperature import getClientIp, merge
from app.service.TemperatureDatSave import validate_request, prepare_data_collection, collect_data, clean_data, \
    prepare_data_storage, store_data
from app.service.TemperatureDataService import measurement_file_save
from app.service.ToolCommonService import get_tool_dictionarys
from tools.utils.FileUtils import get_filename_without_extension

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@temperature_bp.route('/index', methods=['GET'])
def temperature_upload():
    try:
        # 燃料类型
        measurement_file_source_list = get_tool_dictionarys(dict_type='file_source')
        measurement_file_oem_list = get_tool_dictionarys(dict_type='OEM_TYPE')
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
        "file_name": get_filename_without_extension(file_name),
        "save_path": save_file
    }
    operation_code, operation_result = measurement_file_save(params=params)

    if "success" != operation_code:
        return jsonify({'status': 'failure', 'save_file': '', 'msg': operation_result})

    return jsonify({'status': 'success', 'save_file': save_file, 'msg': operation_result})


@temperature_bp.route('/todb', methods=['POST'])
def todb():
    data = request.get_json()
    file_source = data['file_source']
    measure_file_path = data['save_file']

    last_id, error_response = validate_request(data)
    if error_response:
        return error_response

    existing_columns, mdf = prepare_data_collection(last_id, measure_file_path)
    if not existing_columns:
        return mdf  # mdf here is the error response

    df, error_response = collect_data(mdf, existing_columns)
    if error_response:
        return error_response

    df, rename_mapping = clean_data(df,existing_columns)

    params, columns_in_db = prepare_data_storage(db_pool, 'chip_temperature', df, last_id, file_source,rename_mapping)
    if not params:
        return columns_in_db  # columns_in_db here is the error response

    return store_data(db_pool, 'chip_temperature', params, df)
