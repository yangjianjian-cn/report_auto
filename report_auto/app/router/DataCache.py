__coding__ = "utf-8"

from app import db_pool
from tools.utils.DBOperator import query_table


def getDictType(dict_type: str):
    query_sql = 'select dict_value,dict_name from tool_dictionary where dict_type = %s order by dict_id'
    params = [dict_type]  # 初始化参数列表
    # 执行查询
    tool_dictionary_dict: dict = query_table(db_pool, query=query_sql, params=params)
    return tool_dictionary_dict


def getDictTypeDetail(dict_value: str):
    query_sql = """
        select tdd.item_value,tdd.item_label
        from tool_dictionary td
        join tool_dictionary_detail tdd on td.dict_id = tdd.dict_id
        where td.dict_value = %s
        order by detail_id
    """
    params = [dict_value]  # 初始化参数列表
    # 执行查询
    tool_dictionary_detail_dict: dict = query_table(db_pool, query=query_sql, params=params)
    return tool_dictionary_detail_dict
