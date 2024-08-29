#!/usr/bin/env python
# coding=utf-8

import logging
import mimetypes
import os

from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify, send_file, make_response

from tools.parser.dat_csv_doc import dat_csv_docx, docx_zip

app = Flask(__name__)

# 加载 .env 文件
load_dotenv()
# 从环境变量中读取配置
app.config['input_path'] = os.getenv('input_path')
app.config['output_path'] = os.getenv('output_path')
app.config['docx_path'] = os.getenv('docx_path')
app.config['zip_path'] = os.getenv('zip_path')
app.config['template_path'] = os.getenv('template_path')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@app.route('/', methods=['GET'])
def index():
    return render_template('./index.html')


@app.route('/upload', methods=['POST'])
def upload():
    upload_file = request.files['file']
    filename = upload_file.filename

    input_path = app.config['input_path']
    save_path = os.path.join(input_path, filename)

    upload_file.save(save_path)
    upload_file.close()
    print("文件已上传:", save_path)
    return jsonify({'upload_part': True})


# 下载报告
@app.route('/report_download', methods=['GET'])
def report_download():
    fileName = request.args.get('fileName')
    docx_path = app.config['docx_path']
    # 检查 docx_path 是否为空
    if not docx_path:
        logging.error({'generate_report_fail': f'The docx_path is empty.'})
    # 检查 datPath 是否存在
    if not os.path.exists(docx_path):
        logging.error({'generate_report_fail': f"Error: The directory '{docx_path}' does not exist."})

    zip_path = app.config['zip_path']
    # 检查 output_path 是否为空
    if not zip_path:
        logging.error({'generate_report_fail': f'The zip_path is empty.'})
    if not os.path.exists(zip_path):
        os.makedirs(zip_path)

    logging.info(f"Input path is valid: {docx_path}")
    logging.info(f"Output path is valid and created if needed: {zip_path}")
    try:
        zip_file_name, zip_file_path = docx_zip(docx_path, zip_path,fileName)
    except Exception as e:
        logging.error({'generate_report_fail': {e}})

    # 获取文件 MIME 类型
    mime_type, _ = mimetypes.guess_type(zip_file_name)
    mime_type = mime_type or 'application/zip'
    content_disposition = 'attachment; filename*=UTF-8\'\'{}'.format(zip_file_name)

    response = make_response(send_file(zip_file_path, mimetype=mime_type))
    response.headers['Content-Disposition'] = content_disposition

    return response


# 生成报告
@app.route('/generate_report', methods=['POST'])
def generate_report():
    dat_path = app.config['input_path']
    # 检查 datPath 是否为空
    if not dat_path:
        return jsonify({'generate_report_fail': f'The input path is empty'})

    # 检查 datPath 是否存在
    if not os.path.exists(dat_path):
        return jsonify({'generate_report_fail': f"Error: The directory '{dat_path}' does not exist."})

    output_path = app.config['output_path']
    # 检查 output_path 是否为空
    if not output_path:
        return jsonify({'generate_report_fail': f'The output path is empty.'})

    os.makedirs(output_path, exist_ok=True)  # exist_ok=True 表示如果目录已存在则不报错

    logging.info(f"Input path is valid: {dat_path}")
    logging.info(f"Output path is valid and created if needed: {output_path}")

    # 生成报告
    try:
        dat_csv_docx(dat_path, output_path)
    except Exception as e:
        return jsonify({'generate_report_fail': {e}})

    return jsonify({'generate_report_success': output_path})


if __name__ == '__main__':
    app.run(debug=False, threaded=True)

main = app