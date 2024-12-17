__coding__ = "utf-8"

import logging
import os

from flask import render_template
from flask import request, jsonify

from app.router import report_bp
from app.service.IOTestReportService import get_iotest_tplt_list, iotest_tplt_batch_save, iotest_tplt_del, \
    truncate_iotest_tplt, filter_unwanted_keys, prepare_params, iotest_tplt_update
from tools.utils.FtpUtils import FTPUploader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
        where_params: dict = {"id", id}
        ope_rlt, ope_msg = iotest_tplt_update(table=table, set_params=set_params, where_params=where_params)
        return jsonify({"success": ope_rlt, "message": ope_msg}), 200 if ope_rlt else 500
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)}), 500


# 一键上传
@report_bp.route('/iotest/oneKeyUpload', methods=['POST'])
def one_key_upload():
    try:
        data = request.get_json()
        local_directory_path = data['localDirectoryPath']

        if not os.path.isdir(local_directory_path):
            return jsonify({'success': False, 'message': 'Invalid directory path'})

        # 配置FTP服务器信息
        ftp_host = 'your_ftp_server_address'
        ftp_user = 'your_ftp_username'
        ftp_password = 'your_ftp_password'
        remote_root_dir = '/remote/directory/path'

        uploader = FTPUploader(ftp_host, ftp_user, ftp_password, remote_root_dir)
        uploader.traverse_and_upload(local_directory_path)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
