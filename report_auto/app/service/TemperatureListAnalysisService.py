from typing import Mapping, Union

from pandas import DataFrame

from app import db_pool
from pojo import TemperatureVariable
from tools.utils.DBOperator import query_table, insert_data, batch_save, update_table, delete_from_tables_by_in, \
    delete_from_tables
from tools.utils.DateUtils import get_current_datetime_yyyyMMddHHmmss


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


# 文件列表(分页)
# def get_measurement_file_list_page(fileId: str = None, start=None, end=None, query_params=None):
#     # 构建基础查询语句
#     query_sql = '''
#         SELECT file_name, id, source as fuel_type, DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS create_time,project_name,ecu_hw,oem,vehicle_model,vehicle_number,sap_number,software,quantitative_variable,statistical_variable,remark
#         FROM measurement_file
#         WHERE 1 = 1
#     '''
#     # 如果提供了 fileId，则添加额外的过滤条件
#     params = []  # 初始化参数列表
#     if fileId:
#         # 将 fileId 字符串分割成列表
#         id_list = [int(id.strip()) for id in fileId.split(',')]
#         # 添加 IN 子句到查询语句
#         query_sql += ' AND id IN ({})'.format(','.join(['%s'] * len(id_list)))
#         # 将 id 列表添加到参数列表
#         params.extend(id_list)
#     if query_params:
#         pass
#
#     # 添加排序子句
#     query_sql += ' ORDER BY update_time DESC'
#     # 如果提供了分页参数，则添加 LIMIT 和 OFFSET 子句
#     if start is not None and end is not None:
#         query_sql += ' LIMIT %s OFFSET %s'
#         params.append(end - start)  # 每页数据量
#         params.append(start)  # 起始位置
#     # 执行查询
#     measurement_file_list = query_table(db_pool, query=query_sql, params=params)
#
#     # 计算总记录数
#     params.clear()
#     count_sql = 'SELECT COUNT(1) as total FROM measurement_file'
#     if fileId:
#         count_sql += ' WHERE id IN ({})'.format(','.join(['%s'] * len(id_list)))
#         params.extend(id_list)
#
#     total_count_df: DataFrame = query_table(db_pool, query=count_sql, params=params)
#     total_count = total_count_df[0].get("total")
#
#     return total_count, measurement_file_list
#
#
# # 获取测量文件列表(不分页)
# def get_measurement_file_list(fileId: str = None):
#     # 构建基础查询语句
#     query_sql = " SELECT file_name, id, source,special_columns,oem,quantitative_variable,statistical_variable,remark FROM measurement_file "
#
#     # 如果提供了 fileId，则添加额外的过滤条件
#     params = []  # 初始化参数列表
#     if fileId:
#         # 将 fileId 字符串分割成列表
#         id_list = [int(id.strip()) for id in fileId.split(',')]
#         # 添加 IN 子句到查询语句
#         query_sql += ' WHERE id IN ({})'.format(','.join(['%s'] * len(id_list)))
#         # 将 id 列表添加到参数列表
#         params.extend(id_list)
#
#     # 添加排序子句
#     query_sql += ' ORDER BY id DESC'
#
#     # 执行查询
#     measurement_file_list = query_table(db_pool, query=query_sql, params=params)
#     return measurement_file_list


# 编辑每个测量文件的统计量和定量变量
def temperature_variables_edit(temperatureVariable: TemperatureVariable):
    table = "measurement_file"

    set_params: Mapping[str, str] = {}
    if temperatureVariable.quantitative_variable:
        set_params["quantitative_variable"] = temperatureVariable.quantitative_variable
    if temperatureVariable.statistical_variable:
        set_params["statistical_variable"] = temperatureVariable.statistical_variable

    where_params: Mapping[str, int] = {}
    where_params["id"] = temperatureVariable.measurement_file_id

    return update_table(db_pool, table=table, set_params=set_params, where_params=where_params)


def del_chip_temperatures(fileId: int):
    param: Mapping[str, Union[int]] = {"file_id", fileId}
    oprlt, opmsg = delete_from_tables(db_pool,"chip_temperature", param)
    return  oprlt, opmsg