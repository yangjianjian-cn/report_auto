__coding__ = "utf-8"

import logging
from typing import Dict, List

from tools.utils.DBOperator import query_table, query_table_sampling

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def temperature_duration(file_id: str):
    cur_time_diffs: map = {}
    cur_total_minutes: float = 0
    file_ids_int = [int(file_id) for file_id in file_id.split(',')]
    file_ids_str_for_query = ', '.join(map(str, file_ids_int))

    table_name = ' chip_temperature '
    columns = ' ROUND((MAX(timestamps) - MIN(timestamps)) / 60, 2) AS time_difference_in_minutes '

    temperature_intervals = range(-40, 140, 5)  # 包含-40到140
    # 遍历温度区间
    for i in range(len(temperature_intervals) - 1):
        start_temp = temperature_intervals[i]
        end_temp = temperature_intervals[i + 1]
        where_clause = f' where file_id IN ({file_ids_str_for_query})  AND TECU_t BETWEEN {start_temp} AND {end_temp}'
        result_dicts = query_table(table_name, columns, where=where_clause)
        if len(result_dicts) > 0:
            time_difference_in_minutes = result_dicts[0].get('time_difference_in_minutes')
            cur_time_diffs[f"{start_temp}-{end_temp}"] = time_difference_in_minutes
    if cur_time_diffs:
        cur_total_minutes = sum(cur_time_diffs.values())
    return cur_time_diffs, cur_total_minutes


def modify_records(records):
    modified_records = []
    for record in records:
        modified_record = {key: (value if -100 <= value <= 200 else 0) for key, value in record.items()}
        modified_records.append(modified_record)
    return modified_records


def temperature_chip(selected_columns: list, file_id: str):
    file_ids_int = [int(file_id) for file_id in file_id.split(',')]
    file_ids_str_for_query = ', '.join(map(str, file_ids_int))
    result_dicts = query_table_sampling(selected_columns, file_ids_str_for_query)
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
