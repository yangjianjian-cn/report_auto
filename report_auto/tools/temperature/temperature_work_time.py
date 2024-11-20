__coding__ = "utf-8"

import logging
import multiprocessing
from typing import Dict, List

import numpy as np
import pandas as pd
from pandas import DataFrame

from app import db_pool
from tools.utils.DBOperator import query_table, query_table_sampling, query_table_by_sql
from tools.utils.MathUtils import relative_difference_chip, difference_chip

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


def process_file(file_ids: list, measurement_source: str, grouped_special_columns: dict):
    # 构建参数列表
    placeholders = ",".join(map(str, file_ids))
    try:
        # 初始化一个字典来存储每个温度区间的总分钟数
        cur_time_diffs_tecut = defaultdict(float)
        cur_time_diffs_tc1th9 = defaultdict(float)

        logging.info(f"file_id:{placeholders}")

        # ECU TECU_t  temperature duration
        if 'TECU_t' in grouped_special_columns:
            query_sql = f"""
                  SELECT TECU_group AS TECU_T, ROUND( (MAX(timestamps) - MIN(timestamps)) /60,2)  AS timestamps
                    FROM
                        ( SELECT
                            CONCAT(FLOOR((TECU_t + 40) / 5) * 5 - 40, '-', FLOOR((TECU_t + 40) / 5) * 5 - 35) AS TECU_group,timestamps
                            FROM chip_temperature
                            WHERE file_id ={placeholders} 
                        )TMP
                    GROUP BY TECU_group
                    order by TECU_T
            """
            results_df: DataFrame = query_table_by_sql(db_pool, query_sql=query_sql)
            results_df = results_df.dropna(axis=1, how='all')  # 剔除所有值都为 None 的列
            logging.info(f"TECU_T:{len(results_df)}")

            if 'TECU_T' in results_df.columns:
                cur_time_diffs_tecut = results_df.set_index('TECU_T')['timestamps'].to_dict()
                logging.info(f"TECU_t温度时长:{cur_time_diffs_tecut}")

        # ECU Ambient temperature (X3)
        if "X3" in grouped_special_columns:
            X3_list: list = grouped_special_columns["X3"]
            for x3 in X3_list:
                query_sql = f"""
                        SELECT X3_group AS X3, ROUND( (MAX(timestamps) - MIN(timestamps)) / 60, 2) AS timestamps
                        FROM
                            ( SELECT
                                CONCAT(FLOOR(({x3} + 40) / 5) * 5 - 40, '-', FLOOR(({x3} + 40) / 5) * 5 - 35) AS X3_group, timestamps
                                FROM chip_temperature
                                WHERE file_id = {placeholders}
                            ) TMP
                        GROUP BY X3
                        ORDER BY X3
                    """

                results_df: DataFrame = query_table_by_sql(db_pool, query_sql=query_sql)
                results_df = results_df.dropna(axis=1, how='all')  # 剔除所有值都为 None 的列
                if 'X3' in results_df.columns:
                    cur_time_diffs_tc1th9_1 = results_df.set_index('X3')['timestamps'].to_dict()
                    # 手动合并并累加重复键的值
                    for key, value in cur_time_diffs_tc1th9_1.items():
                        cur_time_diffs_tc1th9[key] += value
                    logging.info(f"X3温度时长:{cur_time_diffs_tc1th9}")

        # ECU Internal Ambient temperature(X2)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    # 计算总的分钟数
    cur_total_minutes_tecut = round(sum(cur_time_diffs_tecut.values()), 2)
    cur_total_minutes_tc1th9 = round(sum(cur_time_diffs_tc1th9.values()), 2)
    return cur_time_diffs_tecut, cur_time_diffs_tc1th9, cur_total_minutes_tecut, cur_total_minutes_tc1th9


def temperature_duration(file_ids_int: list = None, max_workers=None, measurement_source=None,
                         grouped_special_columns: dict = None):
    # 使用 ThreadPoolExecutor 并行处理每个文件
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(
            executor.map(lambda fids: process_file([fids], measurement_source, grouped_special_columns), file_ids_int))
    # 合并所有文件的结果
    combined_time_diffs_tecut = defaultdict(float)
    combined_time_diffs_tc1th9 = defaultdict(float)
    total_minutes_tecut = 0
    total_minutes_tc1th9 = 0

    for time_diffs_tecut, time_diffs_tc1th9, total_minute_tecut, total_minute_tc1th9 in results:
        for interval, minutes in time_diffs_tecut.items():
            combined_time_diffs_tecut[interval] += minutes
        total_minutes_tecut += total_minute_tecut

        for interval, minutes in time_diffs_tc1th9.items():
            combined_time_diffs_tc1th9[interval] += minutes
        total_minutes_tc1th9 += total_minute_tc1th9

    return dict(combined_time_diffs_tecut), total_minutes_tecut, dict(combined_time_diffs_tc1th9), total_minutes_tc1th9


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


def temperature_chip(selected_columns: list, file_ids_int: list, measurement_source: str, kv_chip_dict: dict) -> Dict[str, List]:
    file_ids_str_for_query = ', '.join(map(str, file_ids_int))
    selected_columns_str = ', '.join(map(str, selected_columns))
    result_dicts = query_table_sampling(db_pool, columns=selected_columns_str,
                                        file_ids_str_for_query=file_ids_str_for_query,
                                        measurement_source=measurement_source)
    if result_dicts is None or len(result_dicts) < 1:
        # 返回一个空的 temperature_time 字典
        new_temperature_time = {col: [] for col in selected_columns}
        return new_temperature_time

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
        tecu_temperatures = temperature_time_dc.get('X3', [])

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
    chip_dict_list = chip_dict_1(selected_ids=selected_ids)
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


def chip_dict_1(selected_ids: list[int]) -> dict:
    logging.info("获取芯片字典列表:")

    # 构建SQL查询语句
    # 使用参数化查询防止SQL注入
    placeholders = ', '.join(['%s'] * len(selected_ids))  # 根据selected_ids的数量生成占位符
    query_sql = f"""
        SELECT distinct measured_variable, chip_name, max_allowed_value 
        FROM chip_dict 
        WHERE measured_file_name IN ({placeholders})
    """

    # 参数列表
    params = tuple(selected_ids)

    # 调用query_table函数执行查询
    result_dicts = query_table(db_pool, query=query_sql, params=params)
    logging.info(f"result_dicts:{result_dicts}")
    return result_dicts


def chip_dict(measurement_source: str, measured_file_name: str) -> dict:
    logging.info("获取芯片字典列表:")
    # 使用参数化查询防止SQL注入
    query_sql = """
        SELECT measured_variable, chip_name, max_allowed_value 
        FROM chip_dict 
        WHERE status = %s AND source = %s 
    """
    if measured_file_name:
        query_sql = query_sql + " AND measured_file_name=%s "
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
    filtered_column_list = list(filter(lambda x: x not in ['id', 'file_id', 'source', 'timestamps'], column_list))
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

    logging.debug(f"获取芯片阈值:{max_sql}")
    max_query_rslt_df = query_table_by_sql(db_pool, query_sql=max_sql)
    # 删除所有值为 None 的列
    max_query_rslt_df = max_query_rslt_df.dropna(axis=1, how='all')
    # # 重置索引
    results_df = max_query_rslt_df.reset_index()
    # 为列起别名
    results_df = results_df.rename(columns={'index': 'Measurement_Point'})
    logging.info(results_df)

    return results_df


# def calculate_time_diff(df, column_name, temperature_intervals):
#     time_diffs = defaultdict(float)
#     for start_temp, end_temp in zip(temperature_intervals, temperature_intervals[1:]):
#         mask = (df[column_name] >= start_temp) & (df[column_name] < end_temp)
#         filtered_df = df[mask]
#         if not filtered_df.empty:
#             time_diff = (filtered_df['timestamps'].max() - filtered_df['timestamps'].min()) / 60
#             time_diffs[f'{start_temp} ~ {end_temp}'] = round(time_diff, 2)
#     return time_diffs

def calculate_time_diff(df, column_name, temperature_intervals, batch_size=100000):
    time_diffs = defaultdict(float)
    num_batches = len(df) // batch_size + (len(df) % batch_size > 0)

    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = (i + 1) * batch_size
        batch_df = df.iloc[start_idx:end_idx]

        for start_temp, end_temp in zip(temperature_intervals, temperature_intervals[1:]):
            mask = (batch_df[column_name] >= start_temp) & (batch_df[column_name] < end_temp)
            if mask.any():
                filtered_timestamps = batch_df.loc[mask, 'timestamps'].values
                if len(filtered_timestamps) > 0:
                    time_diff = (np.max(filtered_timestamps) - np.min(filtered_timestamps)) / 60
                    time_diffs[f'{start_temp} ~ {end_temp}'] += round(time_diff, 2)

    return time_diffs
