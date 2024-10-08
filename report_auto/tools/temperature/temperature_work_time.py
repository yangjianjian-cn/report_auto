__coding__ = "utf-8"

import logging
from collections import defaultdict
from typing import Dict, List

import pandas as pd

from tools.utils.DBOperator import query_table, query_table_sampling

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def temperature_duration(file_id: str):
    file_ids_int = [int(fid) for fid in file_id.split(',')]
    file_ids_str_for_query = ', '.join(map(str, file_ids_int))

    table_name = 'chip_temperature'
    columns = 'file_id, timestamps, TECU_t '
    where_clause = f' WHERE file_id IN ({file_ids_str_for_query})'

    # 一次性查询所有数据
    all_records = query_table(table_name, columns, where=where_clause)

    # 使用pandas DataFrame来处理数据
    df = pd.DataFrame(all_records)

    # 初始化一个字典来存储每个温度区间的总分钟数
    cur_time_diffs = defaultdict(float)

    # 定义温度区间
    temperature_intervals = list(range(-40, 140, 5))

    # 计算每个温度区间的时间差
    for start_temp, end_temp in zip(temperature_intervals, temperature_intervals[1:]):
        mask = (df['TECU_t'] >= start_temp) & (df['TECU_t'] < end_temp)
        filtered_df = df[mask]

        if not filtered_df.empty:
            time_diff = (filtered_df['timestamps'].max() - filtered_df['timestamps'].min()) / 60
            cur_time_diffs[f'{start_temp}-{end_temp}'] = round(time_diff, 2)

    # 计算总的分钟数
    cur_total_minutes = sum(cur_time_diffs.values())

    return dict(cur_time_diffs), cur_total_minutes


def modify_records(records):
    # 将记录转换为DataFrame
    df = pd.DataFrame(records)

    # 应用条件，将不在范围内的值设置为0
    for column in df.columns:
        df[column] = df[column].apply(lambda x: x if -100 <= x <= 200 else 0)

    # 转换回记录列表
    modified_records = df.to_dict('records')

    return modified_records


def temperature_chip(selected_columns: list, file_id: str):
    file_ids_int = [int(file_id) for file_id in file_id.split(',')]
    file_ids_str_for_query = ', '.join(map(str, file_ids_int))

    result_dicts = query_table_sampling(selected_columns, file_ids_str_for_query)
    if result_dicts is None or len(result_dicts) < 1:
        # 返回一个空的 temperature_time 字典
        return {col: [] for col in selected_columns}

    result_dicts = modify_records(result_dicts)
    # 使用字典推导式来创建结果字典
    temperature_time: Dict[str, List] = {
        col: [row[col] for row in result_dicts] for col in result_dicts[0].keys()
    }
    return temperature_time


def create_data_structure(temperature_time_dc1, sensors: list):
    result = []
    tecu_temperatures = temperature_time_dc1['TECU_t']

    for sensor in sensors:
        series_data = []
        for i, temp in enumerate(temperature_time_dc1[sensor]):
            series_data.append({"name": sensor, "value": [temp, tecu_temperatures[i]]})
        result.append({"name": sensor, "type": "line", "data": series_data})

    return result
