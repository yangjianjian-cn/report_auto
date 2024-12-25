__coding__ = "utf-8"

import logging
import mimetypes
import os

from flask import render_template, make_response, send_file
from flask import request, jsonify

from app import env_template_path, env_output_path, env_input_path
from app.router import report_bp
from app.router.DataCache import getDictType, getDictTypeDetail
from app.service.IOTestReportService import get_iotest_projectType, s_qry_report_auto_pro
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.dat_csv_common import counter_report
from tools.parser.dat_csv_doc import docx_merge, mst_header_page, dat_csv_docx
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

    project_types:list=[]
    tool_dictionary_dict_list: dict = {}
    page = 'mst_report.html'
    if '1' == test_project_type:
        page = 'mst_report.html'
    elif '2' == test_project_type:
        tool_dictionary_dict_list: list = getDictType('signal_type')
        # 测试项目:下拉列表
        project_types: list = get_iotest_projectType()
        page = 'io_test_report.html'
    # 渲染模板
    return render_template(
        page,
        test_project_type_id=test_project_type,

        test_project_type_val=test_project_type_info['val'],
        test_project_type_name=test_project_type_info['name'],

        counters=merged_dict,  # 不展开字典
        tool_dictionary_dict_list=tool_dictionary_dict_list,
        project_types=project_types
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

        project_file: str = data["project_file"]
        module_name: str = data["module_name"]
        params_dict: dict = {
            "project_file": project_file,
            "module_name": module_name
        }
        result_dicts_list: list[dict] = s_qry_report_auto_pro(params_dict)
        if len(result_dicts_list) > 0:
            moduleId: int = result_dicts_list[0].get("id")
        else:
            moduleId: int = 0

        tool_dictionary_detail_list: list = getDictTypeDetail(moduleId)
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

    clientIp = get_client_ip(request)
    output_path: str = env_output_path
    output_path = os.path.join(output_path, clientIp)

    merge_path = env_template_path
    merge_path = os.path.join(merge_path, clientIp)

    if not output_path:
        logging.error({'generate_report_fail': f'The docx_path is empty.'})
    output_path = os.path.join(output_path, test_team)

    merge_path = os.path.join(merge_path, 'merge')
    if not merge_path:
        logging.error({'generate_report_fail': f'The merge_path is empty.'})

    if 'MST_Test' == test_team:
        output_path = os.path.join(output_path, 'docx')
    else:
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

            merge_file_name, merge_file_path = docx_merge(output_path, merge_path, fileName, clientIp)

        else:
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
    logging.info("生成报告:generate_report...")
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
            test_area_dataLabel=test_area_dataLabel,
            clientIp=client_ip
        )
        ret_sucess_msg, ret_err_msg = dat_csv_docx(req_data)
    except Exception as e:
        raise e
        return jsonify({'generate_report_error': {e}})

    return jsonify({'generate_report_success': ret_sucess_msg, 'generate_report_failed': ret_err_msg})
