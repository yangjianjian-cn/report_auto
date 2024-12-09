__coding__ = "utf-8"

from typing import Mapping, Union

from app import db_pool
from tools.utils.DBOperator import query_table, batch_save, execute_ddl_sql, \
    delete_from_tables_by_list, update_table


# io_test测试模板列表
def get_iotest_tplt_list(table_name: str) -> list[dict]:
    query = f"""
        SELECT
            id,pin_no,hw_pin,short_name,io_comment,long_name,information_hints,device_encapsulation,
            level1,checked_values,preparation_1,stimulation_1,tester,measurements_1,
            level2,checked_errors,preparation_2,stimulation_2,measurements_2,
            level3,debouncing_healing,preparation_3,stimulation_3,measurements_3,
            level4,error_substitute,preparation_4,stimulation_4,measurements_4,
            update_time
        FROM {table_name} ORDER BY id DESC
    """
    iotest_tplt_list: list[dict] = query_table(db_pool, query=query, params=None, conn=None)
    return iotest_tplt_list


# 批量保存iotest_tplt数据到数据库
def iotest_tplt_batch_save(table_name: str = None, data: list = None) -> tuple:
    return batch_save(db_pool, table_name, data)


def iotest_tplt_del(table: str, param: Mapping[str, Union[int, str]]):
    ope_rlt, ope_msg = delete_from_tables_by_list(db_pool, table, param)
    return ope_rlt, ope_msg


def truncate_iotest_tplt(del_sql: str):
    return execute_ddl_sql(db_pool, del_sql)


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
        "error_substitute", "preparation_4", "stimulation_4", "measurements_4"
    ]

    params = []
    for tplt_item in tplt_save_list:
        tplt_dict = {field: tplt_item.get(field, '') for field in db_fields}
        params.append(tplt_dict)
    return params


def iotest_tplt_update(table: str = None, set_params: Mapping[str, any] = None, where_params: Mapping[str, any] = None):
    return update_table(db_pool, table, set_params, where_params)
