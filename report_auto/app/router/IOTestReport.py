__coding__ = "utf-8"

import logging
import os
from collections import defaultdict
from typing import Tuple, Dict, List, Any

from flask import render_template
from flask import request, jsonify

from app.router import report_bp
from app.service.IOTestReportService import get_iotest_tplt_list, iotest_tplt_batch_save, iotest_tplt_del, \
    truncate_iotest_tplt, filter_unwanted_keys, prepare_params, s_get_iotest_pins, \
    s_get_iotest_scenario, s_get_report_auto_pro, s_save_report_auto_pro, s_qry_report_auto_pro, iotest_tplt_update, \
    get_iotest_projectType, qry_rpr_auto_pro, s_get_iotest_checklist_columns, save_iotest_checklist, save_rpr_auto_pro, \
    clean_ioTestChecklistData, clean_reportAuto_Data, modify_rpr_auto_pro
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
    if not module_name:
        result_dicts: list[dict] = s_get_report_auto_pro(project_file)
        if len(result_dicts) > 0:
            module_name_dict = result_dicts[0]
            module_name = module_name_dict.get("module_name", "")

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
        dataId: int = data['id']
        field: str = data['field']
        value: str = data['value']

        set_params: dict[str, str] = {field: value}
        where_params: dict[str, int] = {"id": dataId}

        ope_rlt, ope_msg = iotest_tplt_update(table=table, set_params=set_params, where_params=where_params)
        return jsonify({"success": ope_rlt, "message": ope_msg})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)})


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


@report_bp.route('/iotest/del/pro_module', methods=['POST'])
def del_module_pin():
    pro_module_json = request.get_json()

    project_file: str = pro_module_json["project_type"]
    module_name: str = pro_module_json["module_name"]

    sqlParam: dict[str, str] = {"project_file": project_file, "module_name": module_name}
    db_rslt, db_msg, db_data = clean_ioTestChecklistData(sqlParam)
    if db_rslt:
        clean_reportAuto_Data(sqlParam)
    logging.info("%s,%s,%s", db_rslt, db_msg, db_data)

    return jsonify({"success": db_rslt, "message": db_msg, "data": db_data})


@report_bp.route('/iotest/modify/pro_module', methods=['POST'])
def modify_module_pin():
    pro_module_json = request.get_json()

    project_file: str = pro_module_json["project_type"]
    module_name: str = pro_module_json["module_name"]
    moduleId: str = pro_module_json["moduleId"]

    sqlParam: dict[str, str] = {"project_file": project_file, "module_name": module_name, "moduleId": moduleId}
    db_rslt, db_msg = modify_rpr_auto_pro(sqlParam)
    logging.info("%s,%s,%s", db_rslt, db_msg)

    return jsonify({"success": db_rslt, "message": db_msg})


@report_bp.route('/iotest_report_inherit', methods=['GET'])
def iotest_report_inherit():
    current_project_type: str = request.args.get("project_type", "")
    project_types: list[dict] = get_iotest_projectType()
    # 列表project_types移除current_project_type
    if current_project_type:
        project_types[:] = [project for project in project_types if project['project_file'] != current_project_type]
    return render_template("iotest_report_inherit.html", project_types=project_types,
                           current_project_type=current_project_type)


@report_bp.route('/iotest_report_inherit/ok', methods=['POST'])
def iotest_report_inherit_submit():
    parent_project = request.form.get("parent_project", "")
    parent_project_version = request.form.get("version", "")
    remark = request.form.get("remark", "")
    current_project = request.form.get("current_project_type")

    param: dict[str, str] = {"current_project": current_project,
                             "remark": remark,
                             "parent_project": parent_project,
                             "parent_project_version": parent_project_version}
    logging.info(f"{param}")

    # 为避免单击确定按钮，重复保存，需要先清空一下
    sqlParam: dict[str, str] = {"project_file": current_project}
    db_rslt, db_msg, db_data = clean_ioTestChecklistData(sqlParam)
    if db_rslt:
        clean_reportAuto_Data(sqlParam)
    logging.info("%s,%s,%s", db_rslt, db_msg, db_data)

    # 保存项目 和 测试模块
    db_rslt, db_msg, db_rows = save_rpr_auto_pro(param)
    if not db_rslt:
        return jsonify({"success": db_rslt, "message": db_msg, "rows": db_rows})

    # 查询已保存的项目和模块
    result_dicts: list[dict] = qry_rpr_auto_pro(param)
    # 使用defaultdict来分组
    grouped_by_project_file = defaultdict(list)

    for item in result_dicts:
        project_file = item['project_file']
        grouped_by_project_file[project_file].append(item)

    # 将defaultdict转换为普通字典（可选）
    grouped_by_project_file_dict = dict(grouped_by_project_file)

    def get_ids_list_by_project(grouped_data: Dict[str, List[Dict[str, Any]]], project_file: str) -> List[int]:
        return [item['id'] for item in grouped_data.get(project_file, [])]

    # 获取CS162_P2154_V100_IO分组的所有模块对应的id列表
    parent_project_ids_list = get_ids_list_by_project(grouped_by_project_file_dict, parent_project)
    logging.info(f"{parent_project}: {parent_project_ids_list}")

    # 获取RBBB分组的所有模块对应的id列表
    current_project_ids_list = get_ids_list_by_project(grouped_by_project_file_dict, current_project)
    logging.info(f"{current_project}: {current_project_ids_list}")

    table_name: str = "io_test_checklist"
    column_names: list[str] = s_get_iotest_checklist_columns(table_name)
    db_rslt, db_msg = save_iotest_checklist(parent_project_ids_list, current_project_ids_list, column_names, table_name)
    return jsonify({"success": db_rslt, "message": db_msg})
