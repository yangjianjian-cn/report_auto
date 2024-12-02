__coding__ = "utf-8"

import logging

from flask import request, jsonify, render_template

from app import db_pool
from app.router import temperature_bp
from app.service.TemperatureDatSave import validate_request, prepare_data_collection, collect_data, clean_data, \
    prepare_data_storage, store_data
from app.service.TemperatureDataService import get_measurement_file_list_page, get_measurement_file_list, \
    temperature_variables_edit
from app.service.TemperatureListAnalysisService import del_chip_temperatures
from app.service.ToolCommonService import get_tool_dictionary_details, get_chip_dict
from constant.ToolConstants import ToolConstants
from pojo.TemperatureVariable import TemperatureVariable
from tools.utils.DBOperator import delete_from_tables

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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

    print(quantitative_variable)
    print(statistical_variable)
    print(remark)

    quantitative_variable_sltlist = get_tool_dictionary_details(ToolConstants.QUANTITATIVE_VARIABLE)
    print(quantitative_variable_sltlist)

    statistical_variable_sltlist = get_tool_dictionary_details(ToolConstants.STATISTICAL_VARIABLE)
    print(statistical_variable_sltlist)

    return render_template('temperature_variables_page.html', measurement_file_id=measurement_file_id,
                           quantitative_variable_str=quantitative_variable,
                           statistical_variable_str=statistical_variable,
                           quantitative_variable_sltlist=quantitative_variable_sltlist,
                           statistical_variable_sltlist=statistical_variable_sltlist,
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


@temperature_bp.route('/analysis', methods=['POST'])
def temperature_analysis():
    data = request.get_json()

    # 1.数据接收与验证
    last_id, error_response = validate_request(data)
    if error_response:
        return error_response

    measurement_file_list:list[dict] = get_measurement_file_list(fileId=last_id)
    if len(measurement_file_list) == 0 :
        return None, jsonify({'generate_report_failed': 'Non-existent data'})

    measure_file_path = data['save_path']
    if not measure_file_path:
        return last_id, jsonify({'generate_report_failed': 'File storage path not found!'})

    # 数据清空，再存储
    op_rlt, op_msg = del_chip_temperatures(last_id)
    if not op_rlt:
        return last_id, jsonify({'generate_report_failed': op_msg})

    # 2.数据采集准备
    existing_columns, mdf = prepare_data_collection(last_id, measure_file_path)
    if not existing_columns:
        return mdf  # mdf here is the error response

    df, error_response = collect_data(mdf, existing_columns)
    if error_response:
        return error_response

    # 3.数据清洗
    df, rename_mapping = clean_data(df)

    # 4.数据存储准备
    params, columns_in_db = prepare_data_storage(db_pool, 'chip_temperature', df, last_id, "",rename_mapping)
    if not params:
        return columns_in_db  # columns_in_db here is the error response
    # 5.数据存储
    return store_data(db_pool, 'chip_temperature', params, df)
