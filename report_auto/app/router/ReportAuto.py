__coding__ = "utf-8"

import logging
import mimetypes
import os

from flask import render_template, make_response, send_file
from flask import request, jsonify

from app import env_template_path, env_output_path, env_input_path
from app.router import report_bp
from app.router.DataCache import getDictType, getDictTypeDetail
from app.service.IOTestReportService import get_iotest_tplt_list, iotest_tplt_batch_save, iotest_tplt_del, \
    truncate_iotest_tplt, filter_unwanted_keys, prepare_params, iotest_tplt_update
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.dat_csv_common import counter_report
from tools.parser.dat_csv_doc import dat_csv_docx, docx_merge, mst_header_page
from tools.utils.FileUtils import validate_filename
from tools.utils.IPUtils import get_client_ip

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@report_bp.route('/<string:test_type>', methods=['GET'])
def index(test_type):
    # 获取查询参数
    test_project_type = test_type

    # 定义测试项目类型的映射表
    test_project_types = {
        '1': {'val': 'MST_Test', 'name': 'MST Test'},
        '2': {'val': 'IO_Test', 'name': 'I/O Test'}
    }

    # 使用默认值防止键不存在的情况
    test_project_type_info = test_project_types.get(test_project_type, {'val': 'MST_Test', 'name': 'MST Test'})

    # 报告统计器
    merged_dict = counter_report(env_template_path)

    tool_dictionary_dict_list: dict = {}
    page = 'mst_report.html'
    if '1' == test_project_type:
        page = 'mst_report.html'
    elif '2' == test_project_type:
        tool_dictionary_dict_list: list = getDictType('signal_type')
        page = 'io_test_report.html'

    # 渲染模板
    return render_template(
        page,
        test_project_type_id=test_project_type,
        test_project_type_val=test_project_type_info['val'],
        test_project_type_name=test_project_type_info['name'],
        counters=merged_dict,  # 不展开字典
        tool_dictionary_dict_list=tool_dictionary_dict_list
    )


@report_bp.route('/1/mst_header_page', methods=['GET'])
def mst_header():
    return render_template('mst_header.html')


@report_bp.route('/1/mst_header/save', methods=['POST'])
def mst_header_submit():
    request_data: dict = request.get_json()

    output_path = os.path.join(env_output_path, get_client_ip(request), 'MST_Test')
    tplt_file_name = "mst_header"
    doc_output_name = "mst_header"

    config_data = ReqPOJO(template_path=env_template_path, output_path=output_path, template_name=tplt_file_name,
                          doc_output_name=doc_output_name)

    mst_header_page(config_data, request_data)

    return jsonify({'is_success': True})


@report_bp.route('/2/dict_type/items', methods=['POST'])
def dict_type_items():
    try:
        data = request.get_json()
        dict_value = data["dict_value"]
        tool_dictionary_detail_list: list = getDictTypeDetail(dict_value)
        return jsonify(tool_dictionary_detail_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 上传文件
@report_bp.route('/upload', methods=['POST'])
def upload():
    upload_file = request.files['file']
    test_team = request.form.get('test_team')
    test_scenario = request.form.get('test_scenario')

    test_area = request.form.get('test_area')
    test_area_dataLabel = request.form.get('test_area_dataLabel')
    logging.info(f'测试团队:{test_team},测试场景:{test_scenario}, 测试区域名称:{test_area},测试区域编码:{test_area_dataLabel}')

    filename = upload_file.filename

    check_rslt = validate_filename(filename, test_team)
    if check_rslt:
        return jsonify({'upload_error': check_rslt})

    input_path = env_input_path
    input_path = os.path.join(input_path, get_client_ip(request))

    if test_team:
        input_path = os.path.join(input_path, test_team)
    if test_scenario:
        input_path = os.path.join(input_path, test_scenario)
    if test_area:
        input_path = os.path.join(input_path, test_area)
    os.makedirs(input_path, exist_ok=True)  # exist_ok=True 表示如果目录已存在则不报错

    save_path = f'{input_path}/{filename}'
    logging.info(f"上传目录:{save_path}")

    upload_file.save(save_path)
    return jsonify({'upload_success': True, 'save_path': save_path})


# 下载报告
@report_bp.route('/report_download', methods=['GET'])
def report_download():
    fileName = request.args.get('fileName')
    test_team = request.args.get('test_team')

    output_path: str = env_output_path
    output_path = os.path.join(output_path, get_client_ip(request))

    merge_path = env_template_path
    merge_path = os.path.join(merge_path, get_client_ip(request))

    if not output_path:
        logging.error({'generate_report_fail': f'The docx_path is empty.'})
    output_path = os.path.join(output_path, test_team)

    merge_path = os.path.join(merge_path, 'merge')
    if not merge_path:
        logging.error({'generate_report_fail': f'The merge_path is empty.'})

    if 'MST_Test' == test_team:
        output_path = os.path.join(output_path, 'docx')
    elif 'IO_Test' == test_team:
        output_path = os.path.join(output_path, 'xlsm')

    # 检查 output_path 是否存在
    if not os.path.exists(output_path):
        logging.error({'generate_report_fail': f"Error: The directory '{output_path}' does not exist."})

    merge_file_name = ''
    merge_file_path = ''
    try:
        if 'MST_Test' == test_team:
            # docx文件打包成zip,下载zip文件
            merge_path = os.path.join(merge_path, test_team)
            if not os.path.exists(merge_path):
                os.makedirs(merge_path)
            logging.info(f"Output path is valid and created if needed: {merge_path}")

            merge_file_name, merge_file_path = docx_merge(output_path, merge_path, fileName)
        elif 'IO_Test' == test_team:
            # 直接下载xlsm文件
            merge_file_name = 'IOTest_Main_Tmplt.xlsm'
            merge_file_path = os.path.join(output_path, merge_file_name)

    except Exception as e:
        logging.error({'generate_report_fail': {e}})

    # 获取文件 MIME 类型
    mime_type, _ = mimetypes.guess_type(merge_file_name)
    mime_type = mime_type or 'application/zip'
    content_disposition = 'attachment; filename*=UTF-8\'\'{}'.format(merge_file_name)

    response = make_response(send_file(merge_file_path, mimetype=mime_type))
    response.headers['Content-Disposition'] = content_disposition

    return response


# 生成报告
@report_bp.route('/generate_report', methods=['POST'])
def generate_report():
    # 1. 解析前端发送的 JSON 数据
    data = request.get_json()

    test_team = data['test_team']
    test_scenario = data['test_scenario']
    test_area = data['test_area']

    if "u_files" in data:
        u_files = data['u_files']
    else:
        u_files = ""

    if "test_area_dataLabel" in data:
        test_area_dataLabel = data["test_area_dataLabel"]
    else:
        test_area_dataLabel = None

    client_ip = get_client_ip(request)

    # 2. dat文件目录
    dat_path = env_input_path
    if not dat_path:
        return jsonify({'generate_report_fail': f'The input path is empty'})

    # output文件目录
    output_path = env_output_path
    if not output_path:
        return jsonify({'generate_report_fail': f'The output path is empty.'})

    # 3. 完整dat_path、csv_path、output_path目录
    dat_path = os.path.join(dat_path, client_ip)
    for subdir in [test_team, test_scenario, test_area]:
        if subdir:
            dat_path = os.path.join(dat_path, subdir)
    if not os.path.exists(dat_path):
        return jsonify({'generate_report_fail': f"Error: The directory '{dat_path}' does not exist."})
    os.makedirs(dat_path, exist_ok=True)

    # 完整csv_path目录
    csv_path = os.path.join(output_path, client_ip)
    for subdir in [test_team, test_scenario, test_area]:
        if subdir:
            csv_path = os.path.join(csv_path, subdir)
    os.makedirs(csv_path, exist_ok=True)

    # 完整output_path目录
    output_path = os.path.join(output_path, client_ip, test_team)

    logging.info(f"dat路径: {dat_path}")
    logging.info(f"csv路径: {csv_path}")
    logging.info(f"输出路径: {output_path}")

    # 生成报告
    try:
        req_data = ReqPOJO(
            dat_path=dat_path,
            output_path=output_path,
            csv_path=csv_path,
            test_team=test_team,
            test_scenario=test_scenario,
            test_area=test_area,
            template_path=env_template_path,
            u_files=u_files,
            test_area_dataLabel=test_area_dataLabel
        )
        ret_sucess_msg, ret_err_msg = dat_csv_docx(req_data)
    except Exception as e:
        return jsonify({'generate_report_error': {e}})

    return jsonify({'generate_report_success': ret_sucess_msg, 'generate_report_failed': ret_err_msg})


# --------------------------------------------------------io_test_测试模板--------------------------------------------------------
@report_bp.route('/iotest/tplt/page', methods=['GET'])
def s_iotest_tplt_page():
    return render_template("iotest_tplt_page.html")


# 查询模板
@report_bp.route('/iotest/tplt/page/data', methods=['GET'])
def s_iotest_tplt_page_data():
    table_name = "io_test_checklist"
    iotest_tplt_list: list[dict] = get_iotest_tplt_list(table_name)
    response_data = {
        "code": 200,
        "msg": "success",
        "data": iotest_tplt_list
    }
    return jsonify(response_data)


# 提交模板
@report_bp.route('/iotest/tplt/page/submit', methods=['POST'])
def s_iotest_tplt_add():
    table_name = "io_test_checklist"
    unwanted_keys = {'LAY_TABLE_INDEX', 'undefined', 'update_time'}  # 定义不想要的键
    try:
        # 获取并解析JSON数据
        data = request.get_json()
        print(data)

        # 数据校验
        if not data or 'data' not in data:
            return jsonify({"success": False, "message": "Invalid data format"})

        # 数据清洗
        iotest_tplt_list: list[dict] = data['data']
        tplt_save_list: list = [filter_unwanted_keys(item, unwanted_keys) for item in iotest_tplt_list]

        # 数据校验
        for item in iotest_tplt_list:
            hw_pin = item.get('hw_pin')
            pin_no = item.get('pin_no')

            if not hw_pin and not pin_no:
                return jsonify({"success": False, "message": " both 'hw_pin' and 'pin_no' set to None. "})
            elif not hw_pin:
                return jsonify({"success": False, "message": " 'hw_pin' set to None."})
            elif not pin_no:
                return jsonify({"success": False, "message": " 'pin_no' set to None. "})

        # 数据清空
        del_sql = f"truncate table {table_name}"
        op_rslt, op_msg = truncate_iotest_tplt(del_sql)
        params: list = prepare_params(tplt_save_list)

        # 数据保存
        if op_rslt:
            operator_rslt = iotest_tplt_batch_save(table_name=table_name, data=params)

        # 返回成功响应
        return jsonify({"success": operator_rslt[0], "message": operator_rslt[1]})
    except Exception as e:
        # 处理其他可能的异常
        return jsonify({"success": False, "message": str(e)})


# 删除模板
@report_bp.route('/iotest/tplt/page/del', methods=['POST'])
def s_iotest_tplt_del():
    table: str = "io_test_checklist"
    try:
        data = request.get_json()
        ids_to_delete = data.get('ids', [])

        # 请求参数校验
        if not isinstance(ids_to_delete, list):
            return jsonify({"success": False, "message": "Invalid 'ids' format. Expected a list."}), 500

        # 过滤掉 None 值
        valid_ids = [i for i in ids_to_delete if i is not None]
        param: dict[str, list[int]] = {"id": valid_ids}
        ope_rlt, ope_msg = iotest_tplt_del(table, param)

        return jsonify({"success": ope_rlt, "message": ope_msg}), 200 if ope_rlt else 500
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)}), 500


# 修改模板
@report_bp.route('/iotest/tplt/page/update', methods=['POST'])
def s_iotest_tplt_update():
    table: str = "io_test_checklist"
    try:
        data = request.get_json()
        id = request.args.get("id")
        set_params: data = {}
        where_params: dict = {"id",id}
        ope_rlt, ope_msg = iotest_tplt_update(table=table, set_params=set_params, where_params=where_params)
        return jsonify({"success": ope_rlt, "message": ope_msg}), 200 if ope_rlt else 500
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)}), 500
