__coding__ = "utf-8"

import os
from typing import List, Dict, Any

from app import db_pool
from pojo.MSTReportEntity import MSTReportEntity
from tools.utils.DBOperator import query_table, insert_entity, update_table


def get_total_num_from_db(csv_file_name: str) -> int:
    """
    根据csv文件名从数据库中获取total_num的值。

    :param db_pool: 数据库连接池
    :param csv_file_name: CSV文件名
    :return: total_num的整数值
    """
    query = "SELECT IFNULL(total_num, 0) AS total_num FROM report_statistics WHERE csv_file_name=%(csv_file_name)s"
    params = {"csv_file_name": csv_file_name}
    report_statistics_list = query_table(db_pool, query=query, params=params)

    # 如果查询结果为空，则返回0
    if not report_statistics_list:
        return 0

    return report_statistics_list[0].get("total_num", 0)


def insert_report_statistics(req_data, doc_output_path: str, csv_file_name: str):
    """
    创建MSTReportEntity对象，并将其插入到数据库中。

    :param db_pool: 数据库连接池
    :param req_data: 请求数据，包含clientIp等信息
    :param doc_output_path: 文档输出路径，用于判断操作结果
    :param csv_file_name: CSV文件名
    """
    # 获取当前总数
    # total_num_int: int = get_total_num_from_db(csv_file_name)

    basename: str = os.path.basename(csv_file_name)  # 获取文件的基本名称
    filename_without_extension, _ = os.path.splitext(basename)

    # 创建MSTReportEntity实例并设置属性
    mst_report_entity = MSTReportEntity()
    mst_report_entity.client_ip = req_data.clientIp
    mst_report_entity.csv_file_name = filename_without_extension.lower()
    mst_report_entity.operator_rslt = "1" if "succeed" not in doc_output_path else "2"
    mst_report_entity.test_type = 'MST'

    # 插入实体到数据库
    table_name: str = "report_statistics"
    result: List[Dict[str, Any]] = get_report_statistics(mst_report_entity.csv_file_name, mst_report_entity.client_ip)
    if len(result) == 0:
        insert_entity(db_pool, table_name, mst_report_entity)
    else:
        total_num_int: int = result[0].get("total_num")
        mst_report_entity.total_num = total_num_int + 1
        update_report_statistics(mst_report_entity)


def update_report_statistics(mst_report_entity: MSTReportEntity):
    table_name: str = "report_statistics"
    where_params = {
        "client_ip": mst_report_entity.client_ip,
        "csv_file_name": mst_report_entity.csv_file_name
    }
    set_params = {
        "operator_rslt": mst_report_entity.operator_rslt,
        "total_num": mst_report_entity.total_num
    }
    update_table(db_pool, table_name, set_params, where_params)


def get_operator_rslt(client_ip: str, file_name: str) -> Dict[str, str]:
    result: List[Dict[str, Any]] = get_report_statistics(file_name, client_ip)
    # 构建文件操作结果字典
    file_operator_rslt = {
        item['csv_file_name']: item['operator_rslt']
        for item in result
    }

    return file_operator_rslt


def get_report_statistics(file_name: str, client_ip: str) -> List[Dict[str, Any]]:
    """
       根据客户端IP和文件名从数据库中获取操作结果。

       :param client_ip: 客户端IP地址
       :param file_name: 文件名字符串，多个文件名用逗号分隔
       :return: 包含文件名和对应操作结果的字典列表
       """

    # 准备文件名列表
    new_file_name_list = []
    for f_name in file_name.split(","):
        basename = os.path.basename(f_name.strip())  # 获取文件的基本名称并去除前后空白
        filename_without_extension, _ = os.path.splitext(basename)
        new_file_name_list.append(filename_without_extension.lower())

    # 如果没有文件名，则返回空列表
    if not new_file_name_list:
        return []

    # 构造SQL查询语句，动态生成占位符
    placeholders = ', '.join(['%s'] * len(new_file_name_list))
    query_sql = f"""
        SELECT csv_file_name, operator_rslt, COALESCE(total_num, 0) as total_num 
        FROM report_statistics 
        WHERE client_ip = %s AND csv_file_name IN ({placeholders})
    """

    # 执行查询并获取结果
    params = [client_ip] + new_file_name_list  # 将client_ip和文件名列表合并为参数列表
    result: List[Dict[str, Any]] = query_table(db_pool, query_sql, params)

    return result
