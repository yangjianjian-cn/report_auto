__coding__ = "utf-8"

import logging
import mimetypes
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Tuple, Dict, List, Any

from asammdf import MDF
from flask import render_template, send_file, make_response
from flask import request, jsonify

from app import env_output_path, env_template_path
from app.router import report_bp
from app.service.IOTestReportService import get_iotest_tplt_list, iotest_tplt_batch_save, iotest_tplt_del, \
    truncate_iotest_tplt, filter_unwanted_keys, prepare_params, s_get_iotest_pins, \
    s_get_iotest_scenario, s_get_report_auto_pro, s_save_report_auto_pro, s_qry_report_auto_pro, iotest_tplt_update, \
    get_iotest_projectType, qry_rpr_auto_pro, s_get_iotest_checklist_columns, save_iotest_checklist, save_rpr_auto_pro, \
    clean_ioTestChecklistData, clean_reportAuto_Data, modify_rpr_auto_pro, s_get_report_auto_pro_byVer
from app.service.iotest.analogue_input_service import simple_electrical_test, analogue_input_level4
from app.service.iotest.levels_analysis_common import level1_simple_electrical_test, level2_error_detection, \
    level3_debouncing_error_healing
from tools.conversion.iotest.analysis_tocsv import write_analysis_tocsv
from tools.conversion.iotest.analysis_todb import IOTestDataInDB
from tools.utils.CsvFileCombineUtil import CSVCombiner
from tools.utils.IPUtils import get_client_ip
from tools.utils.xlsm_utils import find_first_empty_row_after_string

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


# 一键上传
@report_bp.route('/iotest/upload', methods=['POST'])
def iotest_upload():
    test_team = request.form.get('test_team')
    relativePath = request.form.get("relativePath")

    upload_file = request.files['file']
    filename = upload_file.filename
    logging.info(f'测试项目:{test_team},测试文件:{filename},相对路径:{relativePath}')

    # 创建 Path 对象
    path_obj = Path(relativePath)
    # 去掉最后一层（文件名）
    without_filename = path_obj.parent
    # 去掉第一层目录
    # 通过 parts 属性获取路径的所有部分，然后切片去掉第一个部分
    # 最后用 / 将剩下的部分重新组合成一个新的路径
    folder_path: str = Path(*without_filename.parts[1:])
    logging.info(f"folder_path:{folder_path}")

    iotest_output_path: str = os.path.join(env_output_path, "iotest", get_client_ip(request), test_team, folder_path)
    if not os.path.exists(iotest_output_path):
        os.makedirs(iotest_output_path, exist_ok=True)

    iotest_output_file: str = os.path.join(iotest_output_path, filename)
    upload_file.save(iotest_output_file)
    logging.info("iotest_output_file:%s", iotest_output_file)

    return jsonify({'upload_success': True, 'save_path': iotest_output_file})


# 文件校验
@report_bp.route('/iotest/verification', methods=['POST'])
def iotest_verification():
    data = request.get_json()

    response_data = {
        'generate_report_success': [],
        'generate_report_failed': []
    }

    # 1.测试文件是否已配置
    project_file = data['test_team']
    logging.info("测试文件:%s", project_file)
    result_dicts: list[dict] = s_get_report_auto_pro_byVer(project_file)
    if len(result_dicts) == 0:
        response_data['generate_report_failed'].append(f"The first-level directory does not configured: {project_file} <br>")
        return response_data

    # 2. 测试模块是否存在
    iotest_project_path: str = os.path.join(env_output_path, "iotest", get_client_ip(request), project_file)
    # 文件
    module_folder_name: list[str] = [item.name for item in Path(iotest_project_path).iterdir() if item.is_dir()]
    # 数据库
    module_db_name: list[str] = [item['module_name'] for item in result_dicts]

    # 在数据库中已经配置的二级目录
    module_common_elements = [item for item in module_folder_name if item in module_db_name]
    # 未配置的二级目录
    unique_to_module_folder_name = [item for item in module_folder_name if item not in module_common_elements]
    for m in unique_to_module_folder_name:
        iotest_module_path: str = os.path.join(iotest_project_path, m)
        iotest_dat_module_err: str = f"The secondary-level directory does not configured.:{iotest_module_path}"
        response_data['generate_report_failed'].append(iotest_dat_module_err + "<br>")

    # 3.测试PIN角是否配置
    for module in module_common_elements:
        iotest_module_path: str = os.path.join(iotest_project_path, module)
        logging.info(f"测试模块: {module}")

        ioTestDataInDB = IOTestDataInDB()
        result_list_dicts: list[dict] = ioTestDataInDB.get_io_test_data(test_project=project_file,
                                                                        test_scenario=module,
                                                                        test_area_dataLabel=None)
        # 在数据库中已经配置的三级目录
        pin_db_name: list[str] = [item['hw_pin'] for item in result_list_dicts]
        # 文件服务器中的三级目录
        pin_folder_name: list[str] = [item.name for item in Path(iotest_module_path).iterdir() if item.is_dir()]

        pin_common_elements = [item for item in pin_folder_name if item in pin_db_name]
        unique_to_pin_folder_name = [item for item in pin_folder_name if item not in pin_common_elements]
        # 文件中的三级目录未在数据库中配置
        for pin_name in unique_to_pin_folder_name:
            iotest_pin_path: str = os.path.join(iotest_module_path, pin_name)
            iotest_dat_pin_err: str = f"The third-level directory does not configed:{iotest_pin_path}"
            response_data['generate_report_failed'].append(iotest_dat_pin_err + "<br>")

        for pin in pin_common_elements:
            iotest_pin_path: str = os.path.join(iotest_module_path, pin)
            result_dicts: list[dict] = [next((entry for entry in result_list_dicts if entry.get('hw_pin') == pin), {})]

            logging.info("PIN角:%s", iotest_pin_path)
            logging.info("PIN角模板:%s", result_dicts)

            # 4.dat文件转csv
            all_files = list(Path(iotest_pin_path).rglob('*.dat'))
            for file in all_files:
                mdf = MDF(file)
                df = mdf.to_dataframe()
                alias_column_names = {item: item.split('\\')[0] for item in df.columns.tolist()}
                df.rename(columns=alias_column_names, inplace=True)  # 重命名列名

                db_columns_list: list = ioTestDataInDB.csv_needed_columns(result_dicts)  # 检索列，列名小写
                db_columns_lower = {col.lower() for col in db_columns_list}

                # 保留 file_column_list 中在 db_columns_list 中存在的列，并保持原始顺序
                file_column_list: list = df.columns.tolist()
                columns_list = [col for col in file_column_list if col.lower() in db_columns_lower]
                logging.info(f"columns_list:{columns_list}")

                # 4.1 按配置的列检索文件
                df = df[columns_list]

                # 4.2 将dat文件转换成csv文件
                lowercase_filename = file.with_suffix('.csv').name.lower()
                new_csv_file = os.path.join(iotest_pin_path, lowercase_filename)

                with open(new_csv_file, 'w', newline='') as f:
                    df.to_csv(f, index=True)

            # 5.PIN角目录下，相同前缀的csv文件合并成一个
            csv_files = [f for f in os.listdir(iotest_pin_path) if f.endswith('.csv')]
            if not csv_files:
                logging.error(f"Warning: No CSV file was found in {iotest_pin_path}.")  # 如果没有CSV文件，跳过这个PIN
                continue

            # 文件名前缀相同的文件，合并成一个文件
            logging.info("合并文件...")
            prefixes = ['level1', 'level2', 'level3', 'level4']
            combiner = CSVCombiner(iotest_pin_path, prefixes)
            combiner.combine_csvs()

    return jsonify(response_data)


# 报告生成
@report_bp.route('/iotest/generate_report', methods=['POST'])
def iotest_report_generate():
    data = request.get_json()
    response_data = {'generate_report_success': [], 'generate_report_failed': []}

    # 1.测试文件
    project_file = data['test_team']
    logging.info("测试文件:%s", project_file)

    # 2.测试模块
    result_dicts: list[dict] = s_get_report_auto_pro_byVer(project_file)
    if len(result_dicts) == 0:
        response_data["generate_report_failed"] = f"{project_file}'s Test Module is Empty.<br>"
        return response_data

    ioTestDataInDB = IOTestDataInDB()
    # 一级目录
    iotest_project_path: str = os.path.join(env_output_path, "iotest", get_client_ip(request), project_file)

    for module in result_dicts:
        module_name = module['module_name']
        # 二级目录
        iotest_module_path: str = os.path.join(iotest_project_path, module_name)
        if not os.path.exists(iotest_module_path):
            response_data['generate_report_failed'].append(
                f"Path does not match the Configuration: {iotest_module_path}<br>")
            continue
        logging.info("测试模块:%s", module_name)

        # 3.测试PIN角
        result_list_dicts: list[dict] = ioTestDataInDB.get_io_test_data(test_project=project_file,
                                                                        test_scenario=module_name,
                                                                        test_area_dataLabel=None)
        for one_pin in result_list_dicts:
            hw_pin = one_pin['hw_pin']
            # 三级目录
            iotest_pin_path: str = os.path.join(iotest_module_path, hw_pin)
            if not os.path.exists(iotest_pin_path):
                response_data['generate_report_failed'].append(f"Path does not match the Configuration: {iotest_pin_path}.<br>")
                continue
            # 4.PIN角文件存在，分析测量数据，输出测试报告
            try:
                pin_dict: dict = next((item for item in result_list_dicts if item['hw_pin'] == hw_pin), None)
                # 将单个字典转换为 list[dict]
                if pin_dict is not None:
                    pin_dict_list = [pin_dict]
                    analysis_write(iotest_pin_path, module_name, pin_dict_list, response_data, project_file)
            except Exception as e:
                raise e
                logging.error(e)
                continue

    logging.info(f"{response_data}")
    return jsonify(response_data)


# 定义一个辅助函数用于处理各级别的文件
def process_level_file(level: str, file_path: Path, module_name: str, result_dicts: list[dict],
                       response_data: dict[str, list]):
    try:
        logging.info(f">>>>>>{level}")
        if level == "level1":
            if module_name == "Analog Input":
                op_code, op_msg = simple_electrical_test(file_path, result_dicts)
            else:
                op_code, op_msg = level1_simple_electrical_test(file_path, result_dicts)
        else:
            test_func = {
                "level2": level2_error_detection,
                "level3": level3_debouncing_error_healing,
                "level4": analogue_input_level4
            }[level]
            op_code, op_msg = test_func(file_path, result_dicts)

        logging.info(f"{level}:{op_code},{op_msg}")

        if op_code != 1:
            response_data['generate_report_failed'].append(op_msg + "<br/>")

        return op_code

    except Exception as e:
        response_data['generate_report_failed'].append(str(e) + "<br>")
        logging.error(e)
        return 0  # 返回失败状态码


def analysis_write(csv_path: str, module_name: str, result_dicts: list[dict], response_data: dict, project_file: str):
    logging.info(f"PIN角:{csv_path}")
    logging.info(f"PIN角模板:{result_dicts}")

    # 初始化集合
    levels = {f"level{i}": set() for i in range(1, 5)}
    target_files = {'level1.csv', 'level2.csv', 'level3.csv', 'level4.csv'}

    # 处理CSV文件
    csv_files = Path(csv_path).glob('*.csv')
    if not any(csv_files):
        response_data['generate_report_failed'].append(f"No Files In: {csv_path}.<br>")
        logging.error(f"No Files In: {csv_path}")
        return response_data

    for file_path in Path(csv_path).glob('*.csv'):
        file_name = file_path.name.lower()
        logging.info(f"文件:{file_name}")

        if file_name not in target_files:
            continue

        level = file_name.split(".")[0]
        op_code = process_level_file(level, file_path, module_name, result_dicts, response_data)
        levels[level].add(op_code)

    # 准备输出文件
    output_dir = os.path.join(env_output_path, get_client_ip(request), project_file, "xlsm")
    os.makedirs(output_dir, exist_ok=True)  # 确保输出目录存在
    output_file = os.path.join(output_dir, "IOTest_Main_Tmplt.xlsm")
    logging.info(f"输出文件:{output_file}")

    if not os.path.exists(output_file):
        source_file = os.path.join(env_template_path, "template", "IOTest_Main_Tmplt.xlsm")
        shutil.copy2(source_file, output_file)

    # 插入行号
    try:
        insert_rownum = find_first_empty_row_after_string(output_file, module_name)
    except Exception as e:
        raise e
        response_data['generate_report_failed'].append(str(e) + "<br>")

    logging.info(f"insert_rownum:{insert_rownum}")

    if insert_rownum is not None:
        write_analysis_tocsv(output_file, insert_rownum, levels, result_dicts)


# 清空测试报告
@report_bp.route('/iotest/clean_report', methods=['POST'])
def clean_report():
    try:
        data = request.get_json()
        test_project = data.get('test_project')

        if not test_project:
            return jsonify({"message": "No filename provided.", "code": 400})

        # 清除测试报告的逻辑
        report_output_file = os.path.join(env_output_path, get_client_ip(request), test_project, "xlsm",
                                          "IOTest_Main_Tmplt.xlsm")

        if not os.path.exists(report_output_file):
            return jsonify({"message": "Reports directory does not exist.", "code": 404})

        try:
            os.unlink(report_output_file)  # 删除文件
            return jsonify({"message": f"Test report {report_output_file} has been cleared successfully.", "code": 200})
        except Exception as e:
            return jsonify({"message": f"Failed to delete {report_output_file}. Reason: {e}", "code": 500})

    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}", "code": 500})


# 下载IOTest测试报告
@report_bp.route('/iotest/report_download', methods=['GET'])
def iotest_report_download():
    test_team = request.args.get('test_team')
    clientIp = get_client_ip(request)
    output_path: str = env_output_path
    output_path = os.path.join(output_path, clientIp, test_team, 'xlsm')

    # 检查 output_path 是否存在
    if not os.path.exists(output_path):
        logging.error({'generate_report_fail': f"Error: The directory '{output_path}' does not exist."})

    # 直接下载xlsm文件
    merge_file_name = 'IOTest_Main_Tmplt.xlsm'
    merge_file_path = os.path.join(output_path, merge_file_name)

    # 获取文件 MIME 类型
    mime_type, _ = mimetypes.guess_type(merge_file_name)
    content_disposition = 'attachment; filename*=UTF-8\'\'{}'.format(merge_file_name)

    response = make_response(send_file(merge_file_path, mimetype=mime_type))
    response.headers['Content-Disposition'] = content_disposition

    return response
