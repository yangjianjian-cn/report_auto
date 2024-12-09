__coding__ = "utf-8"

import logging
import tempfile

from flask import request, jsonify, render_template

from app.router import temperature_bp
from app.router.Temperature import allowed_file, extract_columns_from_mdf
from app.service.TemperatureDataService import batch_chip_dict_save
from app.service.ToolCommonService import get_chip_dict, \
    chip_dict_del

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# @temperature_bp.route('/configuration/list', methods=['GET'])
# def temperature_configuration():
#     measurement_file_id = request.args.get("file_id")
#     return render_template('temperature_configuration_list.html', measurement_file_id=measurement_file_id)
#
#
# @temperature_bp.route('/configuration_data', methods=['GET'])
# def temperature_configuration_data():
#     measurement_file_id: str = request.args.get('measurement_file_id')
#     configuration_data_list: list[dict] = get_chip_dict(measurement_file_id)
#     # 构建响应数据
#     response_data = {
#         "code": 200,
#         "msg": "success",
#         "data": configuration_data_list
#     }
#     return jsonify(response_data)


# label-name配置页面(默认显示已配置的label-name列表)
@temperature_bp.route('/configuration/page', methods=['GET'])
def temperature_configuration_add_page():
    s_oem = request.args.get("oem")
    file_id = request.args.get("measured_file_id", "")
    last_id: str = file_id if file_id else s_oem  # 文件配置了label，取文件配置的label；若文件未配置，取项目配置的label

    chip_dict_list: list[dict] = get_chip_dict(last_id)
    return render_template('temperature_configuration_page.html', s_oem=s_oem, page_measured_file_id=file_id,
                           chip_dict_list=chip_dict_list)


# 追加 label-name
@temperature_bp.route('/configuration/add', methods=['POST'])
def temperature_configuration_add():
    try:
        s_oem = request.args.get("OEM")
        s_measured_file_id = request.args.get("measured_file_id")
        # 获取前端传递的数据
        data = request.get_json()
        operator_result, operator_msg = batch_chip_dict_save(data=data, s_oem=s_oem,
                                                             s_measured_file_id=s_measured_file_id)
        # 返回成功响应
        return jsonify({"success": operator_result, "message": operator_msg})
    except Exception as e:
        # 返回错误响应
        return jsonify({"success": False, "message": str(e)})


# 删除label-name，入参：deleteIds:list
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


# 获取一个测量文件的label
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
            label_name_columns: list[str] = None
            label_name_alias_columns: list[str] = None
            if file.filename.endswith('.dat') or file.filename.endswith('.mf4'):
                label_name_columns: list[str] = extract_columns_from_mdf(temp_file_path)
                logging.info("提取列:%s", label_name_columns)
                # label_name_alias_columns:list =

            # 删除临时文件
            # os.remove(temp_file_path)

            logging.info(f"columns:{label_name_columns}")

            if label_name_columns is not None:
                # 返回列名称
                return jsonify({"success": True, "message": "Columns extracted successfully", "columns": label_name_columns}), 200
            else:
                return jsonify({"success": False, "message": "Unsupported file format"}), 400
        else:
            return jsonify({"success": False, "message": "File type not allowed"}), 400

    except Exception as e:
        logging.error(f"获取测量量异常: {e}", exc_info=True)
        # 返回错误响应
        return jsonify({"success": False, "message": str(e)}), 500
