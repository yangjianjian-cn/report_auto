__coding__ = "utf-8"

from app import db_pool
from tools.utils.DBOperator import query_table


def getDictType(dict_type: str):
    query_sql = 'select dict_value,dict_name from tool_dictionary where dict_type = %s order by dict_id'
    params = [dict_type]  # 初始化参数列表
    # 执行查询
    tool_dictionary_dict: dict = query_table(db_pool, query=query_sql, params=params)
    return tool_dictionary_dict


def getDictTypeDetail(moduleId: int):
    query_sql = """
        select itc.pin_no as item_value,itc.hw_pin as item_label from io_test_checklist itc
        where module_id = %s
        order by pin_no
    """
    params = [moduleId]  # 初始化参数列表
    # 执行查询
    tool_dictionary_detail_dict: dict = query_table(db_pool, query=query_sql, params=params)
    return tool_dictionary_detail_dict
