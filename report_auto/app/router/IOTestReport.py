__coding__ = "utf-8"

import logging
import os
from typing import Tuple

from flask import render_template
from flask import request, jsonify

from app.router import report_bp
from app.service.IOTestReportService import get_iotest_tplt_list, iotest_tplt_batch_save, iotest_tplt_del, \
    truncate_iotest_tplt, filter_unwanted_keys, prepare_params, iotest_tplt_update, s_get_iotest_pins, \
    s_get_iotest_scenario, s_get_report_auto_pro, s_save_report_auto_pro, s_qry_report_auto_pro
from tools.utils.FtpUtils import FTPUploader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@report_bp.route('/iotest/tplt/page', methods=['GET'])
def s_iotest_tplt_page():
    project_type: str = request.args.get("j_project", "")

    result_dicts_list: list[dict] = s_get_report_auto_pro(project_type)
    if len(result_dicts_list) > 0:
        module_name = result_dicts_list[0].get("module_name")
    else:
        module_name = ""

    return render_template("iotest_tplt_page.html", project_type=project_type, result_dicts_list=result_dicts_list,
                           module_name=module_name)


# 查询模板
@report_bp.route('/iotest/tplt/page/data', methods=['GET'])
def s_iotest_tplt_page_data():
    project_file = request.args.get("project_type", "")
    module_name = request.args.get("module_type", "")

    params: dict = {"project_file": project_file, "module_name": module_name}
    recode_list: list[dict] = s_qry_report_auto_pro(params)
    if len(recode_list) > 0:
        id = recode_list[0].get("id")
        params: dict = {"module_id": id}
        iotest_tplt_list: list[dict] = get_iotest_tplt_list(params)
    else:
        iotest_tplt_list: list[dict] = []

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
        # 获取并解析JSON数据 & 数据校验
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"success": False, "message": "Invalid data format"})

        # 项目和测试模块
        project_type: str = request.args.get("project_type")
        module_name: str = request.args.get("module_name")
        params_dict: dict = {
            "project_file": project_type,
            "module_name": module_name
        }
        result_dicts_list: list[dict] = s_qry_report_auto_pro(params_dict)
        if len(result_dicts_list) > 0:
            moduleId = result_dicts_list[0].get("id")
        else:
            rslt: Tuple = s_save_report_auto_pro(project_type, module_name)
            moduleId = rslt[1]

        iotest_tplt_list: list[dict] = data['data']
        for item in iotest_tplt_list:
            hw_pin = item.get('hw_pin')
            pin_no = item.get('pin_no')
            item["module_id"] = moduleId

            if not hw_pin and not pin_no:
                return jsonify({"success": False, "message": " both 'hw_pin' and 'pin_no' set to None. "})
            elif not hw_pin:
                return jsonify({"success": False, "message": " 'hw_pin' set to None."})
            elif not pin_no:
                return jsonify({"success": False, "message": " 'pin_no' set to None. "})
        logging.info(f"iotest_tplt_list:{iotest_tplt_list}")

        # 数据清空
        del_sql = f"DELETE FROM {table_name} WHERE module_id = {moduleId}"
        op_rslt, op_msg = truncate_iotest_tplt(del_sql)

        # 数据清洗
        tplt_save_list: list = [filter_unwanted_keys(item, unwanted_keys) for item in iotest_tplt_list]
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


# 场景下拉列表
# 入参：测试项目
@report_bp.route('/iotest/scenario', methods=['GET'])
def get_iotest_scenario():
    s_project_file: str = request.args.get("projectFile", "")
    params: dict = {"project_file": s_project_file}
    module_name_list: list[dict[str, str]] = s_get_iotest_scenario(params)
    return jsonify({"success": True, "message": "query success", "record_list": module_name_list})


# PIN角
# 入参：测试项目
@report_bp.route('/iotest/pins', methods=['GET'])
def get_iotest_pins():
    s_project_type: str = request.args.get("project_type", "")
    s_scenario_type: str = request.args.get("scenario_type", "")
    params: dict = {"project_type": s_project_type, "s_scenario_type": s_scenario_type}
    pin_list: list[dict[str, str]] = s_get_iotest_pins(params)
    return pin_list


@report_bp.route('/save/pro_module', methods=['POST'])
def save_report_auto_pro():
    pro_module_json = request.get_json()

    project_type: str = pro_module_json["project_type"]
    module_name: str = pro_module_json["module_name"]
    ret_msg = s_save_report_auto_pro(project_type, module_name)

    ist_msg: str = ret_msg[0]
    last_id: int = ret_msg[1]
    return jsonify({
        "success": False if (last_id is None) else True,
        "message": ist_msg,
        "recordId": last_id
    })
