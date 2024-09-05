import logging
import mimetypes
import os

from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, send_file, make_response

from pojo import RedisCounter
from pojo.MSTReqPOJO import ReqPOJO
from tools.parser.dat_csv_doc import dat_csv_docx, docx_zip
from tools.utils.RedisUtils import getRedisConnector

app = Flask(__name__)

# 加载 .env 文件
load_dotenv()
# 从环境变量中读取配置
app.config['input_path'] = os.getenv('input_path')
app.config['output_path'] = os.getenv('output_path')
app.config['docx_path'] = os.getenv('docx_path')
app.config['zip_path'] = os.getenv('zip_path')
app.config['template_path'] = os.getenv('template_path')
app.config['redis_connector'] = os.getenv('redis_connector')

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

    # 连接Redis并获取计数器
    redis_counter: RedisCounter = getRedisConnector(app.config['redis_connector'])

    # 获取所有需要的计数器值
    counters = {
        'MST_Test': redis_counter.get_value('MST_Test'),
        'IO_Test': redis_counter.get_value('IO_Test'),
        'APP_PL_BR_1': redis_counter.get_value('app_pl_br_1'),
        'Brk_04': redis_counter.get_value('brk_04'),
        'Brk_05': redis_counter.get_value('brk_05'),
        'NGS_06': redis_counter.get_value('ngs_06'),
        'Clth_05': redis_counter.get_value('clth_05'),
        'Clth_06': redis_counter.get_value('clth_06'),
        'analogue_input': redis_counter.get_value('AnalogueInput'),
        'digital_input': redis_counter.get_value('DigitalInput'),
        'PWM_input': redis_counter.get_value('PWM_input'),
        'digital_output': redis_counter.get_value('DigitalOutput'),
        'PWM_output': redis_counter.get_value('PWM_output')
    }

    # 渲染模板
    return render_template(
        './index.html',
        test_project_type_id=test_project_type,
        test_project_type_val=test_project_type_info['val'],
        test_project_type_name=test_project_type_info['name'],
        counters=counters  # 不展开字典
    )


# 上传dat文件
@app.route('/upload', methods=['POST'])
def upload():
    upload_file = request.files['file']
    test_team = request.form.get('test_team')
    test_scenario = request.form.get('test_scenario')
    test_area = request.form.get('test_area')
    logging.info(f'测试团队:{test_team},测试场景:{test_scenario}, 测试区域{test_area}')

    filename = upload_file.filename
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
    return jsonify({'upload_part': True})


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
            template_path=app.config['template_path'],
            redis_connector=app.config['redis_connector']
        )
        final_file_path = dat_csv_docx(req_data)
    except Exception as e:
        return jsonify({'generate_report_fail': {e}})

    return jsonify({'generate_report_success': final_file_path})


if __name__ == '__main__':
    app.run(debug=False, threaded=True)

main = app
