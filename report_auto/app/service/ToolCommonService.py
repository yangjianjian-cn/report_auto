__coding__ = "utf-8"

from typing import Mapping

from app import db_pool
from tools.utils.DBOperator import query_table, delete_from_tables_by_in


# 根据字典类型获取字典项
def get_tool_dictionarys(dict_type: str = 'file_source'):
    # 构建基础查询语句
    query_sql = 'select dict_value,dict_name from tool_dictionary where dict_type = %s order by dict_id'
    params = [dict_type]  # 初始化参数列表
    # 执行查询
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)
    return measurement_file_list


def get_tool_dictionary_details(dict_type: str = 'file_source'):
    # 构建基础查询语句
    query_sql = """
        select item_value,item_label from tool_dictionary_detail
        where dict_id =(select dict_id from tool_dictionary where dict_type = %s )
    """
    params = [dict_type]  # 初始化参数列表
    # 执行查询
    measurement_file_list: list[dict] = query_table(db_pool, query=query_sql, params=params)
    return measurement_file_list


# chip_dict
def get_chip_dict(last_id: str) -> list[dict]:
    query = "select id,measured_variable, chip_name,max_allowed_value from chip_dict where measured_file_name = %s "
    params = (last_id)
    selected_columns_dict: list[dict] = query_table(db_pool, query=query, params=params)

    if len(selected_columns_dict) == 0:
        query = "select id,measured_variable, chip_name,max_allowed_value  from chip_dict where  measured_file_name = (select oem from measurement_file where id =  %s )"
        params = (last_id)
        selected_columns_dict: list[dict] = query_table(db_pool, query=query, params=params)

    if len(selected_columns_dict) == 0:
        # 当查询结果为空时，返回一个空的字符串列表
        return []
    return selected_columns_dict


def chip_dict_del(delete_ids: list[str]):
    table_name: str = "chip_dict"

    # 转换列表中的字符串为整数
    int_ids = [int(id) for id in delete_ids]
    # 将整数列表转换为由逗号分隔的字符串
    int_ids_str = ','.join(str(id) for id in int_ids)

    param: Mapping = {"id": int_ids_str}
    return delete_from_tables_by_in(db_pool, table_name, param)


def chip_dict_in_sql(selected_ids: list[int] = None, project_type: list[str] = None) -> dict:
    # 构建SQL查询语句
    # 使用参数化查询防止SQL注入
    selected_ids_str = [str(id) for id in selected_ids]
    # selected_ids_str.append(project_type)

    placeholders = ', '.join(['%s'] * len(selected_ids_str))  # 根据selected_ids_str的数量生成占位符

    query_sql = f"""
        SELECT distinct measured_variable, chip_name, max_allowed_value 
        FROM chip_dict 
        WHERE measured_file_name IN ({placeholders}) AND measured_variable IS NOT NULL 
    """

    # 参数列表
    params = tuple(selected_ids_str)

    # 调用query_table函数执行查询
    result_dicts = query_table(db_pool, query=query_sql, params=params)

    if len(result_dicts) == 0:
        placeholders = ', '.join(['%s'] * len(project_type))
        query = f"select id,measured_variable, chip_name,max_allowed_value  from chip_dict where measured_file_name IN ({placeholders}) AND measured_variable IS NOT NULL "
        params = tuple(project_type)
        result_dicts: list[dict] = query_table(db_pool, query=query, params=params)

    if len(result_dicts) == 0:
        return []

    return result_dicts
