__coding__ = "utf-8"

import logging

import numpy as np
from pandas import DataFrame

from app import db_pool
from pojo.TemperatureDurationResult import TemperatureDurationResult
from tools.utils.DBOperator import query_table, query_table_by_sql
from tools.utils.MathUtils import relative_difference_chip, difference_chip

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


def process_file(file_ids: list, statistical_variables_dict: dict) -> TemperatureDurationResult:
    result = TemperatureDurationResult()
    placeholders = ",".join(map(str, file_ids))

    # 定义一个通用的查询函数
    def query_and_process(variable_name: str, variable_value: str, category: str):
        query_sql = f"""
            SELECT {variable_name}_group AS {variable_name}, ROUND( (MAX(timestamps) - MIN(timestamps)) / 60, 2) AS timestamps
            FROM
                ( SELECT
                    CONCAT(FLOOR(({variable_value} + 40) / 5) * 5 - 40, '-', FLOOR(({variable_value} + 40) / 5) * 5 - 35) AS {variable_name}_group, timestamps
                    FROM chip_temperature
                    WHERE file_id IN ({placeholders})
                ) TMP
            GROUP BY {variable_name}
            ORDER BY {variable_name}
        """
        logging.info(f"query_sql:{query_sql}")
        results_df: DataFrame = query_table_by_sql(db_pool, query_sql=query_sql)
        results_df = results_df.dropna(axis=1, how='all')
        if variable_name in results_df.columns:
            durations = results_df.set_index(variable_name)['timestamps'].to_dict()
            result.add_durations(durations, category)
            logging.info(f"{category}温度时长:{durations}")

    # 根据需要处理的数据调用通用函数
    if 'TECU_t' in statistical_variables_dict:
        query_and_process('TECU_T', 'TECU_t', 'TECU_T')

    if 'X3' in statistical_variables_dict:
        for x3 in statistical_variables_dict['X3']:
            query_and_process('X3', x3, 'X3')

    if 'X2' in statistical_variables_dict:
        for x2 in statistical_variables_dict['X2']:
            query_and_process('X2', x2, 'X2')

    return result.get_result()


def temperature_duration(file_ids_int: list = None, max_workers=None, statistical_variables_dict: dict = None):
    # 使用 ThreadPoolExecutor 并行处理每个文件
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        temperatureDuration_result_list: list[dict] = \
            list(executor.map(lambda fids: process_file([fids], statistical_variables_dict), file_ids_int))

    logging.info(f"temperatureDuration_result_list:{temperatureDuration_result_list}")

    # 合并所有文件的结果
    combined_time_diffs_tecut_dict: dict = defaultdict(float)
    combined_time_diffs_x3_dict: dict = defaultdict(float)
    combined_time_diffs_x2_dict: dict = defaultdict(float)

    total_minutes_tecut_f: float = 0
    total_minutes_x3_f: float = 0
    total_minutes_x2_f: float = 0

    for temperatureDuration_result_dict in temperatureDuration_result_list:
        tecut_dict: dict = temperatureDuration_result_dict.get('tecut')
        x3_dict: dict = temperatureDuration_result_dict.get('x3')
        x2_dict: dict = temperatureDuration_result_dict.get('x2')

        t_total_minutes_tecut_f: float = temperatureDuration_result_dict.get('total_minutes_tecut', 0.0)
        t_total_minutes_x3_f: float = temperatureDuration_result_dict.get('total_minutes_x3', 0.0)
        t_total_minutes_x2_f: float = temperatureDuration_result_dict.get('total_minutes_x2', 0.0)

        # 累加每个芯片的温度范围持续时间
        for temp_range, duration in tecut_dict.items():
            combined_time_diffs_tecut_dict[temp_range] += duration
        for temp_range, duration in x3_dict.items():
            combined_time_diffs_x3_dict[temp_range] += duration
        for temp_range, duration in x2_dict.items():
            combined_time_diffs_x2_dict[temp_range] += duration

        # 累加总分钟数
        total_minutes_tecut_f += t_total_minutes_tecut_f
        total_minutes_x3_f += t_total_minutes_x3_f
        total_minutes_x2_f += t_total_minutes_x2_f

    return {
        'combined_time_diffs_tecut_dict': combined_time_diffs_tecut_dict,
        'combined_time_diffs_x3_dict': combined_time_diffs_x3_dict,
        'combined_time_diffs_x2_dict': combined_time_diffs_x2_dict,
        'total_minutes_tecut_f': total_minutes_tecut_f,
        'total_minutes_x3_f': total_minutes_x3_f,
        'total_minutes_x2_f': total_minutes_x2_f
    }


def relative_difference(selected_ids: list[int], chip_dict_list: list) -> list[dict]:
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
    for chip in chip_dict_list:
        measured_variable = chip['measured_variable']
        if measured_variable in result_map:
            chip['max_temperature'] = result_map[measured_variable]
            chip['relative_difference_temperature'] = relative_difference_chip(chip['max_allowed_value'],
                                                                               chip['max_temperature'])
            chip['difference_temperature'] = difference_chip(chip['max_allowed_value'], chip['max_temperature'])
    return chip_dict_list


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
    select_clause = ",\n".join([f"ROUND(MAX({col}),3) AS {col}" for col in filtered_column_list])
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
