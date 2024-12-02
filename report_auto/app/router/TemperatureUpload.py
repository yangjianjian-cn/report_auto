__coding__ = "utf-8"

import logging
import os
import tempfile

from flask import request, jsonify, render_template
from werkzeug.utils import secure_filename

from app import db_pool, env_input_path
from app.router import temperature_bp
from app.router.Temperature import getClientIp, merge, allowed_file, extract_columns_from_mdf
from app.service.TemperatureDatSave import validate_request, prepare_data_collection, collect_data, clean_data, \
    prepare_data_storage, store_data
from app.service.TemperatureDataService import measurement_file_save, batch_chip_dict_save
from app.service.ToolCommonService import get_tool_dictionarys, get_chip_dict, \
    chip_dict_del
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
        return jsonify({"success": trueOrFalse, "message": trueOrFalseMsg}), 200 if trueOrFalse else 500
    except Exception as e:
        return jsonify({"success": False, "message": e}), 500


@temperature_bp.route('/configuration/get', methods=['POST'])
def temperature_configuration_get():
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file part"}), 400

        file = request.files['file']

        # 检查文件是否为空
        if file.filename == '':
            return jsonify({"success": False, "message": "No selected file"}), 400

        # 检查文件扩展名
        if file and allowed_file(file.filename):
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name

            # 提取列名称
            columns = None
            if file.filename.endswith('.dat') or file.filename.endswith('.mf4'):
                columns = extract_columns_from_mdf(temp_file_path)

            # 删除临时文件
            # os.remove(temp_file_path)

            logging.info(f"columns:{columns}")

            if columns is not None:
                # 返回列名称
                return jsonify({"success": True, "message": "Columns extracted successfully", "columns": columns}), 200
            else:
                return jsonify({"success": False, "message": "Unsupported file format"}), 400
        else:
            return jsonify({"success": False, "message": "File type not allowed"}), 400

    except Exception as e:
        logging.error(f"获取测量量异常: {e}", exc_info=True)
        # 返回错误响应
        return jsonify({"success": False, "message": str(e)}), 500


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

    df, rename_mapping = clean_data(df)

    params, columns_in_db = prepare_data_storage(db_pool, 'chip_temperature', df, last_id, file_source,rename_mapping)
    if not params:
        return columns_in_db  # columns_in_db here is the error response

    return store_data(db_pool, 'chip_temperature', params, df)
