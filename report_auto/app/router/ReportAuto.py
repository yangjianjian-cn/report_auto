__coding__ = "utf-8"

import logging
import mimetypes
import os

from flask import request, render_template, jsonify, make_response, send_file

from app import main
from app.router import report_bp
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.dat_csv_common import counter_report
from tools.parser.dat_csv_doc import dat_csv_docx, docx_merge
from tools.utils.FileUtils import validate_filename

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
    merged_dict = counter_report(main.config['template_path'])

    # 渲染模板
    return render_template(
        'index.html',
        test_project_type_id=test_project_type,
        test_project_type_val=test_project_type_info['val'],
        test_project_type_name=test_project_type_info['name'],
        counters=merged_dict  # 不展开字典
    )


# 上传文件
@report_bp.route('/upload', methods=['POST'])
def upload():
    upload_file = request.files['file']
    test_team = request.form.get('test_team')
    test_scenario = request.form.get('test_scenario')
    test_area = request.form.get('test_area')
    logging.info(f'测试团队:{test_team},测试场景:{test_scenario}, 测试区域{test_area}')

    filename = upload_file.filename

    check_rslt = validate_filename(filename, test_team)
    if check_rslt:
        return jsonify({'upload_error': check_rslt})

    input_path = main.config['input_path']

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
    output_path = main.config['output_path']
    merge_path = main.config['template_path']
    # 检查 docx_path 是否为空
    if not output_path:
        logging.error({'generate_report_fail': f'The docx_path is empty.'})

    output_path = os.path.join(output_path, test_team)
    merge_path = os.path.join(merge_path, 'merge')
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
            merge_file_name = 'IOTest_Man_Tmplt.xlsm'
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
    # 解析前端发送的 JSON 数据
    data = request.get_json()
    test_team = data['test_team']
    test_scenario = data['test_scenario']
    test_area = data['test_area']
    u_files = data['u_files']

    # dat文件目录
    dat_path = main.config['input_path']
    if not dat_path:
        return jsonify({'generate_report_fail': f'The input path is empty'})

    # test_team
    if test_team:
        dat_path = os.path.join(dat_path, test_team)

    # test_scenario
    if test_scenario:
        dat_path = os.path.join(dat_path, test_scenario)

    # test_area
    if test_area:
        dat_path = os.path.join(dat_path, test_area)

    # 完整dat_path目录
    if not os.path.exists(dat_path):
        return jsonify({'generate_report_fail': f"Error: The directory '{dat_path}' does not exist."})

    # 输出目录: 测试团队/测试场景
    output_path = main.config['output_path']
    if not output_path:
        return jsonify({'generate_report_fail': f'The output path is empty.'})

    csv_path = os.path.join(output_path, test_team)
    csv_path = os.path.join(csv_path, test_scenario)
    csv_path = os.path.join(csv_path, test_area)
    os.makedirs(csv_path, exist_ok=True)

    output_path = os.path.join(output_path, test_team)
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
            template_path=main.config['template_path'],
            u_files=u_files
        )
        ret_sucess_msg, ret_err_msg = dat_csv_docx(req_data)
    except Exception as e:
        return jsonify({'generate_report_error': {e}})

    return jsonify({'generate_report_success': ret_sucess_msg, 'generate_report_failed': ret_err_msg})
