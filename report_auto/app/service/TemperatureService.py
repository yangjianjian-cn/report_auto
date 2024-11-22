from app import db_pool
from tools.utils.DBOperator import query_table, insert_data, batch_save
from tools.utils.DateUtils import get_current_datetime_yyyyMMddHHmmss

'''根据字典类型获取字典项'''


def get_tool_dictionary_details(dict_type: str = 'file_source'):
    # 构建基础查询语句
    query_sql = 'select dict_value,dict_name from tool_dictionary where dict_type = %s order by dict_id'
    params = [dict_type]  # 初始化参数列表
    # 执行查询
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)
    return measurement_file_list


def measurement_file_save(params: dict = None):
    date_time = get_current_datetime_yyyyMMddHHmmss()
    params["create_time"] = date_time
    params["update_time"] = date_time
    table_name: str = "measurement_file"

    # ('success', last_id)
    ret_msg = insert_data(db_pool, table_name, params, conn=None)
    operation_code = ret_msg[0]
    operation_result = ret_msg[1]

    return operation_code, operation_result


def batch_chip_dict_save(data: list, s_oem: str):
    # 处理数据（这里只是一个示例，实际应用中可能需要保存到数据库等）
    for item in data:
        date_time = get_current_datetime_yyyyMMddHHmmss()
        item["create_time"] = date_time
        item["update_time"] = date_time
        item["measured_file_name"] = s_oem

    table_name: str = "chip_dict"

    ret_msg = batch_save(db_pool, table_name, data)
    operation_code = ret_msg[0]
    operation_result = ret_msg[1]

    return operation_code, operation_result


# 获取每个文件采集的信号量和信号量名称
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
