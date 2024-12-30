__coding__ = "utf-8"

# io_test测试模板列表
import logging
from typing import Any, Dict, List
from typing import Mapping, Union

from app import db_pool
from tools.utils.DBOperator import query_table, batch_save, execute_ddl_sql, \
    delete_from_tables_by_list, update_table, insert_data, execute_dml_sql, getAllColsOfTable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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


# 获取指定版本的report_auto_pro
def s_get_report_auto_pro_byVer(project_file: str):
    query_sql = " SELECT id,module_name FROM report_auto_pro WHERE project_file = %s ORDER BY create_time"
    params_list: list = [project_file]
    result_dicts: list[dict] = query_table(db_pool, query=query_sql, params=params_list)
    return result_dicts


def save_rpr_auto_pro(param: dict[str, Any]):
    sql, params = s_rpr_auto_pro_sql(param)
    return execute_dml_sql(db_pool, sql, params)


# rpr_auto_pro表的SQL拼装
def s_rpr_auto_pro_sql(param: dict[str, Any]):
    required_params = ['current_project', 'remark', 'parent_project', 'parent_project_version']
    if not all(key in param for key in required_params):
        raise ValueError("Missing one or more required parameters")

    sql = """
        INSERT INTO report_auto_pro (project_file, module_name, version, remark)
        SELECT %s, module_name, %s, %s
        FROM report_auto_pro
        WHERE project_file = %s
    """

    # 也继承了父项目的版本号
    params = [
        param['current_project'],  # 当前项目名称
        param['parent_project_version'],  # 父项目模块
        param['remark'],  # 备注
        param['parent_project'],  # 父项目名称
    ]

    if 'parent_project_version' in param and param['parent_project_version']:
        sql += " AND version = %s"
        params.append(param['parent_project_version'])  # 父项目版本号

    return sql, params


def qry_rpr_auto_pro(param: dict[str, Any]):
    qry_list: list[str] = []
    qry_list.append(param['parent_project'])
    qry_list.append(param['current_project'])

    query: str = "select id,project_file,module_name from report_auto_pro where project_file in (%s,%s) order by project_file, module_name"
    return query_table(db_pool, query=query, params=qry_list)


def modify_rpr_auto_pro(sqlParam: dict[str, Any]):
    moduleId = sqlParam.get("moduleId")
    module_name = sqlParam.get("module_name")

    table: str = "report_auto_pro"
    set_params: dict = {"module_name": module_name, "id": moduleId}
    where_params: dict = {"id": moduleId}

    return update_table(db_pool, table=table, set_params=set_params, where_params=where_params)


# 获取表table_name中的所有列名
def s_get_iotest_checklist_columns(table_name: str) -> list[str]:
    db_rslt, db_msg, db_data = getAllColsOfTable(db_pool, table_name)
    # 定义要移除的条目
    columns_to_remove = {'id', 'create_time', 'update_time', 'module_id'}
    # 使用列表推导式移除指定条目
    filtered_column_names = [col for col in db_data if col not in columns_to_remove]
    return filtered_column_names


# iotest_checklist中填充数据
def save_iotest_checklist(parent_project_ids_list: list[int], current_project_ids_list: list[int],
                          column_names: list[str], table_name: str):
    # 构建所有列名字符串，添加 module_id 列
    i_all_columns = ','.join(column_names + ['module_id'])

    # 生成并执行插入语句
    for i, (parent_module_id, current_module_id) in enumerate(zip(parent_project_ids_list, current_project_ids_list)):
        # 构建当前行的列名字符串，不包括 module_id
        i_cur_columns = ','.join([f"{col}" for col in column_names])

        # 构建完整的 SQL 插入语句
        iSQL = f"""
        INSERT INTO {table_name} ({i_all_columns})
        SELECT {i_cur_columns}, %s 
        FROM {table_name} 
        WHERE module_id = %s;
        """

        # 使用参数化查询防止 SQL 注入
        params = (current_module_id, parent_module_id)

        # 打印或执行 SQL 语句（这里假设有一个 db_pool 或类似的数据库连接池）
        logging.info(iSQL % params)  # 仅用于调试，实际使用时应执行 SQL 而不是打印

        # 假设你有一个 execute_sql 函数来执行 SQL 语句
        db_rslt, db_msg, db_data = execute_dml_sql(db_pool, iSQL, params)
        if not db_rslt:
            logging.error(f"Failed to execute SQL: {db_msg}")
            return False, db_msg

    return db_rslt, "All insertions successful"


# 清空io_test_checklist表中匹配条件的数据
def clean_ioTestChecklistData(sqlParam: dict[str, str]):
    current_project = sqlParam.get("project_file")
    module_name = sqlParam.get("module_name")

    del_sql = """
    DELETE FROM io_test_checklist  
    WHERE module_id IN ( 
        SELECT id FROM report_auto_pro  WHERE project_file = %s
    """
    params = (current_project,)

    if module_name is not None:
        del_sql += " AND module_name = %s "
        params = (current_project, module_name)
    del_sql += " )"

    try:
        db_rslt, db_msg, db_data = execute_dml_sql(db_pool, del_sql, params)
        return db_rslt, db_msg, db_data
    except Exception as e:
        logging.error(f"Error executing SQL: {e}")
        raise


# 清空表report_auto_pro中匹配条件的数据
def clean_reportAuto_Data(sqlParam: dict[str, str]):
    current_project = sqlParam.get("project_file")
    module_name = sqlParam.get("module_name")

    del_sql = """ 
        DELETE FROM report_auto_pro 
        WHERE project_file = %s 
    """
    params = (current_project,)

    if module_name is not None:
        del_sql += " AND module_name = %s"
        params = (current_project, module_name)

    try:
        db_rslt, db_msg, db_data = execute_dml_sql(db_pool, del_sql, params)
        return db_rslt, db_msg, db_data
    except Exception as e:
        logging.error(f"Error executing SQL in clean_reportAuto_Data: {e}")
        raise
