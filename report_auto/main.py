import logging
import mimetypes
import os

from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, send_file, make_response

from pojo.MSTReqPOJO import ReqPOJO
from tools.common.dat_csv_common import counter_report
from tools.parser.dat_csv_doc import dat_csv_docx, docx_zip
from tools.temperature.temperature_work_time import temperature_duration, temperature_chip
from tools.utils.FileUtils import validate_filename, get_filename_without_extension

app = Flask(__name__)

# 加载 .env 文件
load_dotenv()
# 从环境变量中读取配置
app.config['input_path'] = os.getenv('input_path')
app.config['output_path'] = os.getenv('output_path')
app.config['template_path'] = os.getenv('template_path')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@app.route('/', methods=['GET'])
def index():
    # 获取查询参数
    test_project_type = request.args.get('test_project_type', '1')

    # 定义测试项目类型的映射表
    test_project_types = {
        '1': {'val': 'MST_Test', 'name': 'MST Test'},
        '2': {'val': 'IO_Test', 'name': 'I/O Test'}
    }

    # 使用默认值防止键不存在的情况
    test_project_type_info = test_project_types.get(test_project_type, {'val': 'MST_Test', 'name': 'MST Test'})

    # 报告统计器
    merged_dict = counter_report(app.config['template_path'])

    # 渲染模板
    return render_template(
        './index.html',
        test_project_type_id=test_project_type,
        test_project_type_val=test_project_type_info['val'],
        test_project_type_name=test_project_type_info['name'],
        counters=merged_dict  # 不展开字典
    )


# 上传文件
@app.route('/upload', methods=['POST'])
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

    input_path = app.config['input_path']

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
    print("文件已上传:", save_path)
    return jsonify({'upload_success': True})


# 下载报告
@app.route('/report_download', methods=['GET'])
def report_download():
    fileName = request.args.get('fileName')
    test_team = request.args.get('test_team')
    output_path = app.config['output_path']
    # 检查 docx_path 是否为空
    if not output_path:
        logging.error({'generate_report_fail': f'The docx_path is empty.'})

    output_path = os.path.join(output_path, test_team)
    zip_path = os.path.join(output_path, test_team)
    if 'MST_Test' == test_team:
        output_path = os.path.join(output_path, 'docx')
    elif 'IO_Test' == test_team:
        output_path = os.path.join(output_path, 'xlsm')

    # 检查 output_path 是否存在
    if not os.path.exists(output_path):
        logging.error({'generate_report_fail': f"Error: The directory '{output_path}' does not exist."})

    logging.info(f"Input path is valid: {output_path}")
    try:
        if 'MST_Test' == test_team:
            # docx文件打包成zip,下载zip文件
            zip_path = os.path.join(zip_path, 'zip')
            if not os.path.exists(zip_path):
                os.makedirs(zip_path)
            logging.info(f"Output path is valid and created if needed: {zip_path}")

            file_name, file_path = docx_zip(output_path, zip_path, fileName)
        elif 'IO_Test' == test_team:
            # 直接下载xlsm文件
            file_name = 'IOTest_Man_Tmplt.xlsm'
            file_path = os.path.join(output_path, file_name)

    except Exception as e:
        logging.error({'generate_report_fail': {e}})

    # 获取文件 MIME 类型
    mime_type, _ = mimetypes.guess_type(file_name)
    mime_type = mime_type or 'application/zip'
    content_disposition = 'attachment; filename*=UTF-8\'\'{}'.format(file_name)

    response = make_response(send_file(file_path, mimetype=mime_type))
    response.headers['Content-Disposition'] = content_disposition

    return response


# 生成报告
@app.route('/generate_report', methods=['POST'])
def generate_report():
    # 解析前端发送的 JSON 数据
    data = request.get_json()
    test_team = data['test_team']
    test_scenario = data['test_scenario']
    test_area = data['test_area']

    # dat文件目录
    dat_path = app.config['input_path']
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
    output_path = app.config['output_path']
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
            template_path=app.config['template_path']
        )
        ret_sucess_msg, ret_err_msg = dat_csv_docx(req_data)
    except Exception as e:
        return jsonify({'generate_report_error': {e}})

    return jsonify({'generate_report_success': ret_sucess_msg, 'generate_report_failed': ret_err_msg})


'''
温度数据上传
'''


@app.route('/temperature_uploader', methods=['GET'])
def temperature_uploader():
    return render_template('./temperature_uploader.html')


'''
芯片温度报表
'''


@app.route('/temperature', methods=['GET'])
def temperature():
    fileId = request.args.get('fileId')
    output_path = app.config['output_path']

    # 关联函数 tools.common.dat_csv_common.dat_csv_conversion
    tecu_output_path = os.path.join(output_path, 'HTM', 'csv', 'tecu')
    if not os.path.exists(tecu_output_path):
        return render_template('./error.html', failure_msg='Please confirm whether the file exists.')

    time_diffs, total_minutes = temperature_duration(tecu_output_path, fileId)

    # DC1_Th 去掉'timestamps'列
    selected_columns_dc1: list = ['DC1_Th1', 'DC1_Th2', 'DC1_Th3', 'DC1_Th4', 'DC1_Th5', 'DC1_Th6', 'DC1_Th7',
                                  'DC1_Th8', 'TECU_t']
    dc1_output_path = os.path.join(output_path, 'HTM', 'csv', 'dc1')
    temperature_time_dc1 = temperature_chip(selected_columns_dc1, dc1_output_path, fileId)

    # TC1_Th
    selected_columns_tc1: list = ['TC1_Th1', 'TC1_Th2', 'TC1_Th3', 'TC1_Th4', 'TC1_Th5', 'TC1_Th6', 'TC1_Th7',
                                  'TC1_Th8',
                                  'TC1_Th9', 'TC1_Th10', 'TC1_Th11', 'TC1_Th12', 'TC1_Th13', 'TC1_Th14', 'TC1_Th15',
                                  'TC1_Th16', 'TECU_t']
    tc1_output_path = os.path.join(output_path, 'HTM', 'csv', 'tc1')
    temperature_time_tc1 = temperature_chip(selected_columns_tc1, tc1_output_path, fileId)

    # TC2_Th
    selected_columns_tc2: list = ['TC2_Th1', 'TC2_Th2', 'TC2_Th3', 'TC2_Th4', 'TC2_Th5', 'TC2_Th6', 'TC2_Th7',
                                  'TC2_Th8',
                                  'TC2_Th9', 'TC2_Th10', 'TC2_Th11', 'TC2_Th12', 'TC2_Th13',
                                  'TECU_t']
    tc2_output_path = os.path.join(output_path, 'HTM', 'csv', 'tc2')
    temperature_time_tc2 = temperature_chip(selected_columns_tc2, tc2_output_path, fileId)

    # 渲染到temperature_main.html模板中的数据
    file_map_list: list = []
    file_str_list: list = []
    for dirpath, dirnames, filenames in os.walk(output_path):
        for filename in filenames:
            if filename not in file_str_list:
                p_filename = get_filename_without_extension(filename)
                file_map: map = {}
                file_map['id'] = p_filename
                file_map['title'] = p_filename
                file_map_list.append(file_map)
                file_str_list.append(filename)

    return render_template('./temperature_main.html',
                           total_minutes=total_minutes,
                           time_diffs=time_diffs,
                           temperature_time_dc1_legend=selected_columns_dc1,
                           temperature_time_tc1_legend=selected_columns_tc1,
                           temperature_time_tc2_legend=selected_columns_tc2,
                           temperature_time_dc1=temperature_time_dc1,
                           temperature_time_tc1=temperature_time_tc1,
                           temperature_time_tc2=temperature_time_tc2,
                           file_map_list=file_map_list
                           )


if __name__ == '__main__':
    app.run(debug=False, threaded=True)

main = app
