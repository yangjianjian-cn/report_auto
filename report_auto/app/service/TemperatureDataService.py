import logging
import multiprocessing
from typing import Mapping, List, Dict, Optional

import pandas as pd

from app import db_pool
from pojo import TemperatureVariable
from tools.utils.DBOperator import query_table, insert_data, batch_save, update_table, query_table_sampling
from tools.utils.DateUtils import get_current_datetime_yyyyMMddHHmmss

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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


def batch_chip_dict_save(data: list = None, s_oem: str = None, s_measured_file_id: str = None):
    if s_measured_file_id:
        measured_file_name = s_measured_file_id
    else:
        measured_file_name = s_oem

    i_data_list: list = []
    # 处理数据（这里只是一个示例，实际应用中可能需要保存到数据库等）
    for item in data:
        # 使用 get 方法避免键不存在时抛出异常，同时也可以设置默认值
        measured_variable = item.get('measured_variable', '')
        chip_name = item.get('chip_name', '')
        max_allowed_value = item.get('max_allowed_value', '')
        max_allowed_value = 0.0 if not max_allowed_value else float(max_allowed_value)
        # 如果所有关键字段都为空，则跳过当前循环
        if not (measured_variable and chip_name):
            continue

        item['max_allowed_value'] = max_allowed_value
        date_time = get_current_datetime_yyyyMMddHHmmss()
        item["create_time"] = date_time
        item["update_time"] = date_time
        item["measured_file_name"] = measured_file_name
        i_data_list.append(item)
    logging.debug(f"i_data_list={i_data_list}")

    table_name: str = "chip_dict"
    query_sql = f"select measured_variable,chip_name from {table_name} where measured_file_name = %s"
    params = (measured_file_name,)
    result_dicts: list[dict] = query_table(db_pool, query=query_sql, params=params)
    logging.debug(f"result_dicts={result_dicts}")

    # 创建一个集合来加速查找
    result_set = {(d['measured_variable'], d['chip_name']) for d in result_dicts}

    # 筛选 i_data_list 中的元素
    filtered_i_data_list = [
        item for item in i_data_list
        if (item['measured_variable'], item['chip_name']) not in result_set
    ]

    ret_msg = batch_save(db_pool, table_name, filtered_i_data_list)
    operation_code = ret_msg[0]
    operation_result = ret_msg[1]

    return operation_code, operation_result


# 文件列表(分页)
def get_measurement_file_list_page(fileId: str = None, start=None, end=None, query_params: dict[str] = None):
    # 构建基础查询语句
    query_sql = '''
        SELECT file_name, id, source as fuel_type, DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS create_time,
               project_name, ecu_hw, oem, vehicle_model, vehicle_number, sap_number, software,
               quantitative_variable, statistical_variable, remark
        FROM measurement_file
    '''

    # 初始化参数列表和过滤条件标志
    params = []
    has_conditions = False

    # 如果提供了 fileId，则添加额外的过滤条件
    if fileId:
        id_list = [int(id.strip()) for id in fileId.split(',')]
        if not has_conditions:
            query_sql += ' WHERE '
            has_conditions = True
        else:
            query_sql += ' AND '
        query_sql += 'id IN ({})'.format(','.join(['%s'] * len(id_list)))
        params.extend(id_list)

    if query_params:
        for key in query_params:
            if not has_conditions:
                query_sql += ' WHERE '
                has_conditions = True
            else:
                query_sql += ' AND '
            query_sql += f"{key} = %s"
            params.append(query_params[key])

    # 添加排序子句
    query_sql += ' ORDER BY update_time DESC'

    # 如果提供了分页参数，则添加 LIMIT 和 OFFSET 子句
    if start is not None and end is not None:
        query_sql += ' LIMIT %s OFFSET %s'
        params.append(end - start)  # 每页数据量
        params.append(start)  # 起始位置

    # 执行查询
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)

    # 计算总记录数
    params.clear()
    count_sql = 'SELECT COUNT(1) as total FROM measurement_file'
    if fileId or query_params:
        count_sql += ' WHERE '
        if fileId:
            count_sql += "id IN ({})".format(','.join(['%s'] * len(id_list)))
            params.extend(id_list)
            if query_params:
                count_sql += ' AND '

        if query_params:
            for key in query_params:
                count_sql += f"{key} = %s"
                params.append(query_params[key])

    total_count_df = query_table(db_pool, query=count_sql, params=params)
    total_count = total_count_df[0].get("total")

    return total_count, measurement_file_list


# 获取测量文件列表(不分页)
def get_measurement_file_list(fileId: str = None):
    # 构建基础查询语句
    query_sql = " SELECT file_name, id, source,special_columns,oem,quantitative_variable,statistical_variable,remark,save_path FROM measurement_file "

    print(type(fileId))
    # 如果提供了 fileId，则添加额外的过滤条件
    params = []  # 初始化参数列表
    if fileId:
        # 将 fileId 字符串分割成列表
        id_list = [int(id.strip()) for id in fileId.split(',')]
        # 添加 IN 子句到查询语句
        query_sql += ' WHERE id IN ({})'.format(','.join(['%s'] * len(id_list)))
        # 将 id 列表添加到参数列表
        params.extend(id_list)

    # 添加排序子句
    query_sql += ' ORDER BY update_time DESC'

    # 执行查询
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)
    return measurement_file_list


# 编辑每个测量文件的统计量和定量变量
def temperature_variables_edit(temperatureVariable: TemperatureVariable):
    table = "measurement_file"

    set_params: Mapping[str, str] = {}
    if temperatureVariable.quantitative_variable:
        set_params["quantitative_variable"] = temperatureVariable.quantitative_variable
    if temperatureVariable.statistical_variable:
        set_params["statistical_variable"] = temperatureVariable.statistical_variable
    if temperatureVariable.remark:
        set_params["remark"] = temperatureVariable.remark

    date_time = get_current_datetime_yyyyMMddHHmmss()
    set_params["update_time"] = date_time

    where_params: Mapping[str, int] = {}
    where_params["id"] = temperatureVariable.measurement_file_id

    return update_table(db_pool, table=table, set_params=set_params, where_params=where_params)


# 构建测量变量列表
# 数据详情页面-离散图和折线图
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


def temperature_chip(selected_columns: list, file_ids_int: list, kv_chip_dict: dict) -> Dict[
    str, List]:
    file_ids_str_for_query = ', '.join(map(str, file_ids_int))
    selected_columns_str = ', '.join(map(str, selected_columns))
    result_dicts = query_table_sampling(db_pool, columns=selected_columns_str,
                                        file_ids_str_for_query=file_ids_str_for_query)
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


def process_sensor(sensor, temperature_line_dict: Dict[str, List], quantitative_temperatures: list):
    if sensor not in temperature_line_dict:
        return None

    sensor_temperatures = temperature_line_dict[sensor]
    min_length = min(len(quantitative_temperatures), len(sensor_temperatures))

    series_data = [[sensor_temperatures[i], quantitative_temperatures[i]] for i in range(min_length)]
    emphasis = {'focus': 'series'}
    markArea = {'silent': 'true', 'itemStyle': {'color': 'transparent', 'borderWidth': 1, 'borderType': 'dashed'},
                'data': [[{'name': '', 'xAxis': 'min', 'yAxis': 'min'}, {'xAxis': 'max', 'yAxis': 'max'}]]}
    # markPoint = {'data': [{'type': 'max', 'name': 'Max'},{'type': 'min', 'name': 'Min'}]}
    return {"name": sensor, "type": "scatter", "emphasis": emphasis, "data": series_data,
            "markArea": markArea}


def create_data_structure(temperature_line_dict: Dict[str, List], temperature_legend_list: list[str],
                          quantitative_variable_str: str,
                          num_processes=None):
    quantitative_temperatures: list = temperature_line_dict.get(quantitative_variable_str, [])
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_sensor,
                               [(sensor, temperature_line_dict, quantitative_temperatures) for sensor in
                                temperature_legend_list])

    # 过滤掉 None 结果
    results = [res for res in results if res is not None]

    return results


def process_temperature_data(measured_variables_list: List[str],
                             quantitative_variable_list: List[str],
                             selected_ids: List[int],
                             kv_chip_dict: Dict) -> (List[str], Dict[str, List], List):
    quantitative_variable_name: str = quantitative_variable_list[0]
    quantitative_variable_code: Optional[str] = next(
        (key for key, value in kv_chip_dict.items() if value == quantitative_variable_name), quantitative_variable_name)
    measured_variables_list.extend([quantitative_variable_code])
    measured_variables = list(set(measured_variables_list))
    measured_variables.append('timestamps')

    # 获取温度随时间变化的数据
    temperature_line_dict: dict[str, list] = temperature_chip(selected_columns=measured_variables,
                                                              file_ids_int=selected_ids,
                                                              kv_chip_dict=kv_chip_dict)

    # 处理返回的数据
    temperature_legend_list: list[str] = [key for key in temperature_line_dict if key != 'timestamps']

    # 创建数据结构
    temperature_scatter_list = create_data_structure(temperature_line_dict, temperature_legend_list,
                                                     quantitative_variable_name,
                                                     num_processes=len(selected_ids))

    return temperature_legend_list, temperature_line_dict, temperature_scatter_list
