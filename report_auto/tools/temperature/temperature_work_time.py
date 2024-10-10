__coding__ = "utf-8"

import logging
import multiprocessing
from typing import Dict, List

import pandas as pd
from pandas import DataFrame

from app import chipNamesConfig
from tools.utils.DBOperator import query_table, query_table_sampling, query_table_by_sql
from tools.utils.MathUtils import relative_difference_chip

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


def process_file(file_ids: list):
    # 查询多个文件的数据
    table_name = 'chip_temperature'
    columns = 'file_id, timestamps, TECU_t'
    file_ids_str_for_query = ', '.join(map(str, file_ids))
    where_clause = f' WHERE file_id IN ({file_ids_str_for_query})'

    try:
        records = query_table(table_name, columns, where=where_clause)
        df = pd.DataFrame(records)

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
    except Exception as e:
        logging.error(f"An error occurred: {e}")

    # 计算总的分钟数
    cur_total_minutes = sum(cur_time_diffs.values())

    return cur_time_diffs, cur_total_minutes


def temperature_duration(file_ids_int: list, max_workers=None):
    # file_ids_int = [int(fid) for fid in file_id.split(',')]

    # 使用 ThreadPoolExecutor 并行处理每个文件
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda fids: process_file([fids]), file_ids_int))

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

    # 应用条件，将不在范围内的值设置为0
    for column in df.columns:
        df[column] = df[column].apply(lambda x: x if -100 <= x <= 200 else 0)

    # 转换回记录列表
    modified_records = df.to_dict('records')

    return modified_records


def temperature_chip(selected_columns: list, file_ids_int: list):
    # file_ids_int = [int(file_id) for file_id in file_id.split(',')]
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

    # 预先构建映射表
    key_mapping = {key: chipNamesConfig.get('chip_names', key) for key in temperature_time.keys()}

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

    series_data = [{"name": sensor, "value": [sensor_temperatures[i], tecu_temperatures[i]]} for i in range(min_length)]

    return {"name": sensor, "type": "line", "data": series_data}


def create_data_structure(temperature_time_dc1, sensors_list: list, num_processes=None):
    tecu_temperatures = temperature_time_dc1.get('TECU_t', [])
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_sensor,
                               [(sensor, temperature_time_dc1, tecu_temperatures) for sensor in sensors_list])

    # 过滤掉 None 结果
    results = [res for res in results if res is not None]

    return results


def str_to_list(sensors_str: str) -> List[str]:
    # 将字符串分割成列表
    selected_columns_dc1_list: List[str] = sensors_str.split(',')

    # 创建一个新的列表，存储替换后的列名
    sensors_list: List[str] = []

    for column in selected_columns_dc1_list:
        try:
            new_column = chipNamesConfig.get('chip_names', column.strip())
            sensors_list.append(new_column)
        except KeyError as e:
            logging.error(f"Key not found: {column}")
            sensors_list.append(column)  # 如果找不到键，保留原值

    return sensors_list


# table_name: str, columns: str, where: str
def relative_difference() -> list[dict]:
    # 芯片字典(包含芯片名称、芯片温度阈值)
    chip_dict_list = chip_dict()

    # 查看每个芯片的最大测量温度
    max_rlt_df = max_query()
    df_transposed = max_rlt_df.T
    result_map = df_transposed[0].to_dict()

    # 遍历 chip_dict_list，并从 data_map 中查找每个 measured_variable 对应的值
    # 然后将这些值添加到 chip_dict_list 中的新列 max_temperature 中
    for chip in chip_dict_list:
        measured_variable = chip['measured_variable']
        if measured_variable in result_map:
            chip['max_temperature'] = result_map[measured_variable]
            chip['difference_temperature'] = relative_difference_chip(chip['max_allowed_value'],
                                                                      chip['max_temperature'])
    return chip_dict_list


def chip_dict():
    table_name = " chip_dict "
    columns = " measured_variable, chip_name,max_allowed_value "
    whereClause = " where status = '1' "
    result_dicts = query_table(table_name, columns, whereClause)
    return result_dicts


def max_query() -> DataFrame:
    max_sql = """
            SELECT
            ROUND(MAX(DC1_Th1)) AS DC1_Th1,
            ROUND(MAX(DC1_Th2)) AS DC1_Th2,
            ROUND(MAX(DC1_Th3)) AS DC1_Th3,
            ROUND(MAX(DC1_Th4)) AS DC1_Th4,
            ROUND(MAX(DC1_Th5)) AS DC1_Th5,
            ROUND(MAX(DC1_Th6)) AS DC1_Th6,
            ROUND(MAX(DC1_Th7)) AS DC1_Th7,
            ROUND(MAX(DC1_Th8)) AS DC1_Th8,
            ROUND(MAX(TC1_Th1)) AS TC1_Th1,
            ROUND(MAX(TC1_Th2)) AS TC1_Th2,
            ROUND(MAX(TC1_Th3)) AS TC1_Th3,
            ROUND(MAX(TC1_Th4)) AS TC1_Th4,
            ROUND(MAX(TC1_Th5)) AS TC1_Th5,
            ROUND(MAX(TC1_Th6)) AS TC1_Th6,
            ROUND(MAX(TC1_Th7)) AS TC1_Th7,
            ROUND(MAX(TC1_Th8)) AS TC1_Th8,
            ROUND(MAX(TC1_Th9)) AS TC1_Th9,
            ROUND(MAX(TC1_Th10)) AS TC1_Th10,
            ROUND(MAX(TC1_Th11)) AS TC1_Th11,
            ROUND(MAX(TC1_Th12)) AS TC1_Th12,
            ROUND(MAX(TC1_Th13)) AS TC1_Th13,
            ROUND(MAX(TC1_Th14)) AS TC1_Th14,
            ROUND(MAX(TC1_Th15)) AS TC1_Th15,
            ROUND(MAX(TC1_Th16)) AS TC1_Th16,
            ROUND(MAX(TC2_Th1)) AS TC2_Th1,
            ROUND(MAX(TC2_Th2)) AS TC2_Th2,
            ROUND(MAX(TC2_Th3)) AS TC2_Th3,
            ROUND(MAX(TC2_Th4)) AS TC2_Th4,
            ROUND(MAX(TC2_Th5)) AS TC2_Th5,
            ROUND(MAX(TC2_Th6)) AS TC2_Th6,
            ROUND(MAX(TC2_Th7)) AS TC2_Th7,
            ROUND(MAX(TC2_Th8)) AS TC2_Th8,
            ROUND(MAX(TC2_Th9)) AS TC2_Th9,
            ROUND(MAX(TC2_Th10)) AS TC2_Th10,
            ROUND(MAX(TC2_Th11)) AS TC2_Th11,
            ROUND(MAX(TC2_Th12)) AS TC2_Th12,
            ROUND(MAX(TC2_Th13)) AS TC2_Th13
        FROM chip_temperature;
    """
    max_query_rslt_df = query_table_by_sql(max_sql)
    # 删除第一行

    # 重置索引
    results_df = max_query_rslt_df.reset_index()

    # 为列起别名
    results_df = results_df.rename(columns={'index': 'Measurement_Point', 0: 'Measurement'})
    return results_df
