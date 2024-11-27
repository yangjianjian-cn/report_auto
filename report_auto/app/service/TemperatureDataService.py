import multiprocessing
from typing import Mapping, List, Dict, Optional

import pandas as pd
from pandas import DataFrame

from app import db_pool
from pojo import TemperatureVariable
from tools.utils.DBOperator import query_table, insert_data, batch_save, update_table, query_table_sampling
from tools.utils.DateUtils import get_current_datetime_yyyyMMddHHmmss

'''根据字典类型获取字典项'''


def get_tool_dictionary_details(dict_type: str = 'file_source'):
    # 构建基础查询语句
    query_sql = 'select dict_value,dict_name from tool_dictionary where dict_type = %s order by dict_id'
    params = [dict_type]  # 初始化参数列表
    # 执行查询
    measurement_file_list = query_table(db_pool, query=query_sql, params=params)
    return measurement_file_list


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
    # table: str, param: Mapping[str, int], conn=None
    del_param: dict = {

    }
    delete_from_tables(table=table_name)
    ret_msg = batch_save(db_pool, table_name, data)
    operation_code = ret_msg[0]
    operation_result = ret_msg[1]

    return operation_code, operation_result


# 获取每个文件采集的信号量和信号量名称
def get_chip_dict(last_id: str) -> list[dict]:
    query = "select id,measured_variable, chip_name,max_allowed_value from chip_dict where measured_file_name = %s "
    params = (last_id)
    selected_columns_dict: list[dict] = query_table(db_pool, query=query, params=params)

    if len(selected_columns_dict) == 0:
        query = "select id,measured_variable, chip_name,max_allowed_value  from chip_dict where  measured_file_name = (select oem from measurement_file where id =  %s )"
        params = (last_id)
        selected_columns_dict: list[dict] = query_table(db_pool, query=query, params=params)

    if len(selected_columns_dict) == 0:
        # 当查询结果为空时，返回一个空的字符串列表
        return []
    return selected_columns_dict


def chip_dict_in_sql(selected_ids: list[int] = None, project_type: list[str] = None) -> dict:
    # 构建SQL查询语句
    # 使用参数化查询防止SQL注入
    selected_ids_str = [str(id) for id in selected_ids]
    # selected_ids_str.append(project_type)

    placeholders = ', '.join(['%s'] * len(selected_ids_str))  # 根据selected_ids_str的数量生成占位符

    query_sql = f"""
        SELECT distinct measured_variable, chip_name, max_allowed_value 
        FROM chip_dict 
        WHERE measured_file_name IN ({placeholders}) AND measured_variable IS NOT NULL 
    """

    # 参数列表
    params = tuple(selected_ids_str)

    # 调用query_table函数执行查询
    result_dicts = query_table(db_pool, query=query_sql, params=params)

    if len(result_dicts) == 0:
        placeholders = ', '.join(['%s'] * len(project_type))
        query = f"select id,measured_variable, chip_name,max_allowed_value  from chip_dict where measured_file_name IN ({placeholders}) AND measured_variable IS NOT NULL "
        params = tuple(project_type)
        result_dicts: list[dict] = query_table(db_pool, query=query, params=params)

    if len(result_dicts) == 0:
        return []

    return result_dicts


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
    query_sql = " SELECT file_name, id, source,special_columns,oem,quantitative_variable,statistical_variable,remark FROM measurement_file "

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


def create_data_structure(temperature_time_dc: DataFrame, sensors_list: list, quantitative_variable_str: str,
                          num_processes=None):
    tecu_temperatures = temperature_time_dc.get(quantitative_variable_str, [])
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.starmap(process_sensor,
                               [(sensor, temperature_time_dc, tecu_temperatures) for sensor in sensors_list])

    # 过滤掉 None 结果
    results = [res for res in results if res is not None]

    return results


def process_temperature_data(prefix: str,
                             measured_variables_list: List[str],
                             quantitative_variable_list: List[str],
                             selected_ids: List[int],
                             kv_chip_dict: Dict) -> (List[str], Dict[str, List], List):
    measured_variables = [var for var in measured_variables_list if var.startswith(prefix)]
    if len(measured_variables) > 0:
        quantitative_variable_name: str = quantitative_variable_list[0]
        quantitative_variable_code: Optional[str] = next(
            (key for key, value in kv_chip_dict.items() if value == quantitative_variable_name),
            quantitative_variable_name)
        measured_variables.extend([quantitative_variable_code])
        measured_variables = list(set(measured_variables))
        measured_variables.append('timestamps')

        # 获取温度随时间变化的数据
        temperature_time = temperature_chip(selected_columns=measured_variables, file_ids_int=selected_ids,
                                            kv_chip_dict=kv_chip_dict)

        # 处理返回的数据
        selected_columns = [key for key in temperature_time if key != 'timestamps']

        # 创建数据结构
        data_structure = create_data_structure(temperature_time, selected_columns, quantitative_variable_name,
                                               num_processes=len(selected_ids))

        return selected_columns, temperature_time, data_structure
    else:
        return [], {}, []
