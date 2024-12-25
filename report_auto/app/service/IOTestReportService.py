__coding__ = "utf-8"

# io_test测试模板列表
from typing import Any, Dict, List
from typing import Mapping, Union

from app import db_pool
from tools.utils.DBOperator import query_table, batch_save, execute_ddl_sql, \
    delete_from_tables_by_list, update_table, insert_data


def filter_unwanted_keys(item, unwanted_keys):
    """
    从字典中移除指定的键。

    :param item: 要过滤的字典
    :param unwanted_keys: 不想要的键列表
    :return: 过滤后的字典
    """
    return {key: (value if value is not None else "") for key, value in item.items() if key not in unwanted_keys}


def prepare_params(tplt_save_list):
    db_fields = [
        "pin_no", "hw_pin", "short_name", "io_comment", "long_name",
        "information_hints", "device_encapsulation", "checked_values",
        "preparation_1", "stimulation_1", "tester", "measurements_1",
        "checked_errors", "preparation_2", "stimulation_2", "measurements_2",
        "debouncing_healing", "preparation_3", "stimulation_3", "measurements_3",
        "error_substitute", "preparation_4", "stimulation_4", "measurements_4", "module_id"
    ]

    params = []
    for tplt_item in tplt_save_list:
        tplt_dict = {field: tplt_item.get(field, '') for field in db_fields}
        params.append(tplt_dict)
    return params


# ############################################################################PIN角模板
# 批量保存iotest_tplt数据到数据库
def iotest_tplt_batch_save(table_name: str = None, data: list = None) -> tuple:
    return batch_save(db_pool, table_name, data)


def iotest_tplt_del(table: str, param: Mapping[str, Union[int, str]]):
    ope_rlt, ope_msg = delete_from_tables_by_list(db_pool, table, param)
    return ope_rlt, ope_msg


def truncate_iotest_tplt(del_sql: str):
    return execute_ddl_sql(db_pool, del_sql)


def iotest_tplt_update(table: str = None, set_params: Mapping[str, any] = None, where_params: Mapping[str, any] = None):
    return update_table(db_pool, table, set_params, where_params)


def qry_iotest_tplt_list(base_query: str, params: Dict[str, Any], orderBy: str):
    # 初始化条件列表和参数列表
    conditions = []
    query_params = []

    # 根据提供的参数生成 WHERE 子句
    if params is not None:
        for key, value in params.items():
            if value is not None:  # 确保值不是 None
                conditions.append(f"{key} = %s")
                query_params.append(value)

    # 如果有条件，则添加到SQL查询中
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    # 添加 ORDER BY 子句
    if orderBy:
        base_query += f" ORDER BY {orderBy} DESC"

    try:
        # 执行查询
        iotest_tplt_list: List[Dict] = query_table(db_pool, query=base_query, params=query_params, conn=None)
        return iotest_tplt_list
    except Exception as e:
        print(f"An error occurred: {e}")
        return []  # 或者你可以选择抛出异常或以其他方式处理错误


# 获取所有pin角模板列表
def get_iotest_tplt_list(params: Dict[str, Any]) -> List[Dict]:
    # 构建SQL查询的基础部分
    base_query = f"""
        SELECT
            id, pin_no, hw_pin, short_name, io_comment, long_name, information_hints, device_encapsulation,
            level1, checked_values, preparation_1, stimulation_1, tester, measurements_1,
            level2, checked_errors, preparation_2, stimulation_2, measurements_2,
            level3, debouncing_healing, preparation_3, stimulation_3, measurements_3,
            level4, error_substitute, preparation_4, stimulation_4, measurements_4,
            update_time
        FROM io_test_checklist
    """
    orderBy: str = "update_time"
    return qry_iotest_tplt_list(base_query, params, orderBy)


# 获取项目类型
def get_iotest_projectType() -> list:
    base_query = " select distinct project_file from report_auto_pro "
    params: dict = None
    orderBy: str = None
    return qry_iotest_tplt_list(base_query, params, orderBy)


# 项目对应的测试场景列表
# params:dict={"project_type":project_type}
def s_get_iotest_scenario(params):
    base_query_sql: str = " select  module_name  as moduleName from report_auto_pro "
    orderBy: str = " create_time "
    return qry_iotest_tplt_list(base_query_sql, params, orderBy)


# 获取所有pin角
# 入参：项目类型、测试场景(测试模块)
def s_get_iotest_pins(params):
    base_query_sql: str = " select pin_no as item_value,hw_pin as item_label from  io_test_checklist "
    orderBy: str = None
    return qry_iotest_tplt_list(base_query_sql, params, orderBy)


# 获取测试文件
def s_get_report_auto_pro(project_file: str):
    query_sql = " SELECT id,module_name FROM report_auto_pro WHERE project_file = %s ORDER BY create_time"
    params_list: list = [project_file]
    result_dicts: list[dict] = query_table(db_pool, query=query_sql, params=params_list)
    return result_dicts


def s_save_report_auto_pro(project_type: str, module_name: str):
    table_name: str = "report_auto_pro"
    params: dict = {
        "project_file": project_type,
        "module_name": module_name
    }
    return insert_data(db_pool, table_name, params)


def s_qry_report_auto_pro(params_dict: dict):
    query: str = "select id from report_auto_pro where project_file=%s and module_name = %s"
    params_list: list = list(params_dict.values())
    return query_table(db_pool, query=query, params=params_list)
