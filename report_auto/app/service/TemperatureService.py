from app import db_pool
from tools.utils.DBOperator import query_table


def temperature_configuration_datas(measurement_file_id: str):
    # 初始化查询语句和参数列表
    query_sql = """SELECT id, measured_variable, chip_name, max_allowed_value FROM chip_dict"""
    params = []

    # 如果 measurement_file_name 不为空，添加 WHERE 子句
    if measurement_file_id:
        query_sql += """ WHERE measured_file_name = %s """
        params.append(measurement_file_id)
    else:
        query_sql += """ WHERE measured_file_name is null """

    # 添加排序子句
    query_sql += """ ORDER BY update_time DESC"""

    # 执行查询
    temperature_configuration_list = query_table(db_pool, query=query_sql, params=params)
    return temperature_configuration_list
