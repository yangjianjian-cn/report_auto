__coding__ = "utf-8"

import logging
import multiprocessing
from typing import Dict, List

import pandas as pd
from pandas import DataFrame

from app import db_pool
from tools.utils.DBOperator import query_table, query_table_sampling, query_table_by_sql
from tools.utils.MathUtils import relative_difference_chip, difference_chip

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


def process_file(db_pool, file_ids: list, measurement_source: str, all_special_columns_str: str):
    if 'NG_FILES' == measurement_source:
        all_special_columns_str = all_special_columns_str
    # 构建参数化查询语句
    placeholders = ', '.join(['%s'] * len(file_ids))  # 创建占位符字符串，如 '%s, %s, %s'
    query_sql = f"""
            SELECT file_id, {all_special_columns_str}
            FROM chip_temperature 
            WHERE file_id IN ({placeholders}) 
            AND source = %s
        """
    # 构建参数列表
    params = file_ids + [str(measurement_source)]  # 将 file_ids 和 measurement_source 组合成一个列表

    try:
        logging.info("获取测量数据")
        records = query_table(db_pool, query=query_sql, params=params)
        df = pd.DataFrame(records)

        # 初始化一个字典来存储每个温度区间的总分钟数
        cur_time_diffs = defaultdict(float)

        # 定义温度区间
        temperature_intervals = list(range(-40, 120, 5))

        # 计算每个温度区间的时间差
        for start_temp, end_temp in zip(temperature_intervals, temperature_intervals[1:]):
            if 'NG_FILES' == measurement_source:
                mask = (df['TC1_Th9'] >= start_temp) & (df['TC1_Th9'] < end_temp)
            else:
                mask = (df['TECU_t'] >= start_temp) & (df['TECU_t'] < end_temp)
            filtered_df = df[mask]

            if not filtered_df.empty:
                time_diff = (filtered_df['timestamps'].max() - filtered_df['timestamps'].min()) / 60
                cur_time_diffs[f'{start_temp} ~ {end_temp}'] = round(time_diff, 2)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    # 计算总的分钟数
    cur_total_minutes = round(sum(cur_time_diffs.values()), 2)

    return cur_time_diffs, cur_total_minutes


def temperature_duration(db_pool, file_ids_int: list = None, max_workers=None, measurement_source=None,
                         all_special_columns_str=None):
    # 使用 ThreadPoolExecutor 并行处理每个文件
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(
            executor.map(lambda fids: process_file(db_pool, [fids], measurement_source, all_special_columns_str),
                         file_ids_int))

    # 合并所有文件的结果
    combined_time_diffs = defaultdict(float)
    total_minutes = 0

    for time_diffs, total_minute in results:
        for interval, minutes in time_diffs.items():
            combined_time_diffs[interval] += minutes
        total_minutes += total_minute

    return dict(combined_time_diffs), total_minutes


def modify_records(records):
    # 将记录转换为DataFrame
    df = pd.DataFrame(records)
    # 处理数据：将除 timestamps 列外的值小于 100 或大于 200 的值置为 0
    for column in df.columns:
        if column != 'timestamps':
            df.loc[(df[column] < -100) | (df[column] > 200), column] = 0
    # 转换回记录列表
    modified_records = df.to_dict('records')

    return modified_records


def temperature_chip(selected_columns: list, file_ids_int: list, measurement_source: str, kv_chip_dict: dict):
    file_ids_str_for_query = ', '.join(map(str, file_ids_int))

    result_dicts = query_table_sampling(db_pool, columns=selected_columns,
                                        file_ids_str_for_query=file_ids_str_for_query,
                                        measurement_source=measurement_source)
    if result_dicts is None or len(result_dicts) < 1:
        # 返回一个空的 temperature_time 字典
        return {col: [] for col in selected_columns}

    result_dicts = modify_records(result_dicts)

    # 使用字典推导式来创建结果字典
    temperature_time: Dict[str, List] = {
        col: [row[col] for row in result_dicts] for col in result_dicts[0].keys()
    }
    temperature_time = {k: v for k, v in temperature_time.items() if not all(x is None for x in v)}

    # 构建 key_mapping
    all_keys = set()
    for record in temperature_time:
        all_keys.add(record)
    key_mapping = {key: kv_chip_dict.get(key, key) for key in all_keys}

    # 使用映射表替换 temperature_time 中的键
    new_temperature_time: Dict[str, List] = {
        key_mapping[key]: value for key, value in temperature_time.items()
    }
    return new_temperature_time


def process_sensor(sensor, temperature_time_dc1, tecu_temperatures):
    if sensor not in temperature_time_dc1:
        return None

    sensor_temperatures = temperature_time_dc1[sensor]
    min_length = min(len(tecu_temperatures), len(sensor_temperatures))

    series_data = [[sensor_temperatures[i], tecu_temperatures[i]] for i in range(min_length)]
    emphasis = {'focus': 'series'}
    markArea = {'silent': 'true', 'itemStyle': {'color': 'transparent', 'borderWidth': 1, 'borderType': 'dashed'},
                'data': [[{'name': '', 'xAxis': 'min', 'yAxis': 'min'}, {'xAxis': 'max', 'yAxis': 'max'}]]}
    # markPoint = {'data': [{'type': 'max', 'name': 'Max'},{'type': 'min', 'name': 'Min'}]}
    return {"name": sensor, "type": "scatter", "emphasis": emphasis, "data": series_data,
            "markArea": markArea}


def create_data_structure(temperature_time_dc: DataFrame, sensors_list: list, measurement_source: str,
                          num_processes=None):
    tecu_temperatures = temperature_time_dc.get('TECU_t', [])
    if 'NG_FILES' == measurement_source:
        tecu_temperatures = temperature_time_dc.get('ECU_25(X3)', [])

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_sensor,
                               [(sensor, temperature_time_dc, tecu_temperatures) for sensor in sensors_list])

    # 过滤掉 None 结果
    results = [res for res in results if res is not None]

    return results


# table_name: str, columns: str, where: str
def relative_difference(selected_ids: list[int], measurement_source: str) -> list[dict]:
    # 查看每个芯片的最大测量温度
    max_rlt_df = max_query(selected_ids)
    for column in max_rlt_df.columns:
        # 值小于-100或大于200的值置0
        max_rlt_df.loc[(max_rlt_df[column] < -100) | (max_rlt_df[column] > 200), column] = 0

    df_transposed = max_rlt_df.T
    logging.debug(f"df_transposed:{df_transposed}")
    result_map = df_transposed[0].to_dict()
    logging.debug(f"result_map:{result_map}")

    # 芯片字典
    chip_dict_list = chip_dict(measurement_source=measurement_source)
    for chip in chip_dict_list:
        measured_variable = chip['measured_variable']
        if measured_variable in result_map:
            chip['max_temperature'] = result_map[measured_variable]
            chip['relative_difference_temperature'] = relative_difference_chip(chip['max_allowed_value'],
                                                                               chip['max_temperature'])
            chip['difference_temperature'] = difference_chip(chip['max_allowed_value'], chip['max_temperature'])
    # 过滤掉没有 max_temperature 属性的芯片
    chip_dict_list = [chip for chip in chip_dict_list if 'max_temperature' in chip]
    return chip_dict_list


def chip_dict(measurement_source: str) -> dict:
    logging.info("获取芯片字典列表:")
    # 使用参数化查询防止SQL注入
    query_sql = """
        SELECT measured_variable, chip_name, max_allowed_value 
        FROM chip_dict 
        WHERE status = %s AND source = %s
    """
    # 构建参数列表
    params = ('1', measurement_source)

    # 调用query_table函数执行查询
    result_dicts = query_table(db_pool, query=query_sql, params=params)
    logging.info(f"result_dicts:{result_dicts}")
    return result_dicts


def max_query(selected_ids: list) -> DataFrame:
    logging.info("获取表chip_temperature列名:")
    results_df: DataFrame = query_table_by_sql(db_pool, query_sql="DESCRIBE chip_temperature")
    column_list: list = results_df['Field'].tolist()

    # 去掉指定的列
    filtered_column_list = list(filter(lambda x: x not in ['id', 'file_id', 'source'], column_list))
    logging.info(f"filtered_column_list:{filtered_column_list}")

    # 动态生成 SQL 查询
    select_clause = ",\n".join([f"ROUND(MAX({col})) AS {col}" for col in filtered_column_list])
    max_query_sql = f"""
        SELECT
        {select_clause}
        FROM chip_temperature
    """
    if len(selected_ids) > 0:
        # 将列表转换为逗号分隔的字符串
        selected_ids_str = ','.join(map(str, selected_ids))
        where_clause = f' WHERE file_id IN ({selected_ids_str})'
        max_sql = max_query_sql + where_clause

    logging.info(f"获取芯片阈值:{max_sql}")
    max_query_rslt_df = query_table_by_sql(db_pool, query_sql=max_sql)
    # 删除所有值为 None 的列
    max_query_rslt_df = max_query_rslt_df.dropna(axis=1, how='all')
    # # 重置索引
    results_df = max_query_rslt_df.reset_index()
    # 为列起别名
    results_df = results_df.rename(columns={'index': 'Measurement_Point'})
    logging.info(results_df)

    return results_df
