__coding__ = "utf-8"

import logging
import os
from typing import List, Dict

import pandas as pd
from pandas import DataFrame

from tools.utils.DateUtils import seconds_to_minutes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def temperature_duration(output_path: str, file_id: str):
    if file_id:
        csv_path = os.path.join(output_path, file_id)
    else:
        # 使用 os.walk 遍历目录及其子目录下的所有文件
        # 获取目录下的所有文件
        files = [f for f in os.listdir(output_path) if os.path.isfile(os.path.join(output_path, f))]
        # 获取第一个文件的名称
        csv_path = os.path.join(output_path, files[0])

    df: DataFrame = pd.read_csv(csv_path, encoding='utf8')
    df.sort_values(['TECU_t'])

    temperatures = df['TECU_t'].astype(float)
    timestamps = df['timestamps']

    cur_time_diffs: map = {}
    temperature_intervals = range(-40, 140, 10)  # 包含-40到130
    # 遍历温度区间
    for i in range(len(temperature_intervals) - 1):
        start_temp = temperature_intervals[i]
        end_temp = temperature_intervals[i + 1]

        try:
            # 找到温度首次进入当前区间的索引
            start_index = temperatures[(temperatures >= start_temp) & (temperatures < end_temp)].index[0]

            # 如果end_temp是最后一个区间的上限，则取该区间内的最后一个数据
            if i == len(temperature_intervals) - 2:
                end_index = temperatures[(temperatures >= start_temp) & (temperatures <= end_temp)].index[-1]
            else:
                # 否则，找到温度首次进入下一区间的索引
                end_index = \
                    temperatures[
                        (temperatures >= end_temp) & (temperatures < temperature_intervals[i + 2])].index[0]
        except IndexError:
            logging.error(f"Warning: No data found between {start_temp} and {end_temp} degrees Celsius.")
            continue

        # 计算两个时间戳之间的时间差
        time_diff = timestamps[end_index] - timestamps[start_index]
        cur_time_diffs[f"{start_temp}°C-{end_temp}°C"] = seconds_to_minutes(time_diff)

    cur_total_minutes = sum(cur_time_diffs.values())

    return cur_time_diffs, cur_total_minutes


def temperature_chip(selected_columns: list, output_path: str, file_id: str) -> Dict[str, List]:
    if file_id:
        csv_path = os.path.join(output_path, file_id)
    else:
        # 使用 os.walk 遍历目录及其子目录下的所有文件
        # 获取目录下的所有文件
        files = [f for f in os.listdir(output_path) if os.path.isfile(os.path.join(output_path, f))]
        # 获取第一个文件的名称
        csv_path = os.path.join(output_path, files[0])

    # 加载csv文件
    df: pd.DataFrame = pd.read_csv(csv_path, encoding='utf8')

    # 只加载指定的列
    specific_df = df[selected_columns]

    k = 1000  # 指定每隔多少行抽取一次
    sampled_df = specific_df.iloc[::k]

    # 使用字典推导式来创建结果字典
    temperature_time: Dict[str, List] = {
        col: sampled_df[col].tolist() for col in sampled_df.columns
    }

    data_structure = create_data_structure(temperature_time, selected_columns)
    return data_structure


def create_data_structure(temperature_time_dc1,sensors: list):
    result = []
    tecu_temperatures = temperature_time_dc1['TECU_t']

    for sensor in sensors:
        series_data = []
        for i, temp in enumerate(temperature_time_dc1[sensor]):
            series_data.append({"name": sensor, "value": [temp, tecu_temperatures[i]]})
        result.append({"name": sensor, "type": "line", "data": series_data})

    return result
