import logging
import operator
from typing import List, Dict

import pandas as pd
from pandas import DataFrame

from tools.utils.MathUtils import get_fifth_bit, get_third_bit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# #########数字量输出-level1
# 1-passed 2-failed 3-na 4-nottested
def level1_simple_electrical_test(csv_file: str, result_dicts: List[dict]) -> str:
    # 1.数据采集
    df_selected = pd.read_csv(csv_file, encoding='utf8')

    # 2.数据清洗
    # 填充 NaN 值为 0
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"实时电压观测量:{uRaw}")
    if not uRaw:
        return 2, "Level1 column 'measurements_1' not configured"

    df_selected[uRaw] = df_selected[uRaw].fillna(0)
    result_set = set(df_selected[uRaw])
    logging.info(f"实时电压观测值:{result_set}")

    if len(result_set) > 1:
        return 1, "success"
    elif len(result_set) == 0:
        return 3, "n/a"
    else:
        return 2, "The voltage value has not changed"


# #########数字量输出-level2故障检测函数入口
# 1-passed 2-failed 3-na 4-nottested
def level2_error_detection(csv_file: str, result_dicts: List[Dict]):
    def error_detection(is_high: bool) -> List[int]:
        df_selected = pd.read_csv(csv_file, encoding='utf8')
        measurements_2_str = get_measurements_2(result_dicts)
        if not measurements_2_str:
            return 2, "Level2 observation 'measurements_2' not configured"

        preparation_2_str = result_dicts[0].get("preparation_2")
        if not preparation_2_str:
            return 2, "Level2: column 'preparation_2' not configured."
        df_selected[f'is_level2_{"high" if is_high else "low"}'] = df_selected.apply(
            lambda row: check_row_new(row, result_dicts, is_high), axis=1
        )

        df_selected_error: DataFrame = df_selected[df_selected[f'is_level2_{"high" if is_high else "low"}'] == True]
        if len(df_selected_error) == 0:
            return 3, "Data exceeding the limit was not found"

        return process_measurements(measurements_2_str, df_selected_error)

    logging.info("超上限")
    upper_code, upper_msg = error_detection(True)

    logging.info("低下限")
    lower_code, lower_msg = error_detection(False)

    ret_msg = upper_msg if upper_msg else lower_msg
    # 有1个成功就成功
    if upper_code == 1 or lower_code == 1:
        return 1, ret_msg
    # 有1个失败就失败
    elif upper_code == 2 or lower_code == 2:
        return 2, ret_msg
    # 都不适应，赋值n/a
    elif upper_code == 3 and lower_code == 3:
        return 3, ret_msg
    # 都未测试，赋值 not tested
    elif upper_code == 4 and lower_code == 4:
        return 4, ret_msg


# #########数字量输出-level2
# 1-passed 2-failed 3-na 4-nottested
def check_row_new(row, result_dicts, is_high):
    measurements_1 = result_dicts[0].get("measurements_1")
    preparation_2_str = result_dicts[0].get("preparation_2")

    preparation_2_list = preparation_2_str.splitlines()
    preparation_2_value = preparation_2_list[0 if is_high else 1]
    logging.debug("电压阈值观测量:%s", preparation_2_value)

    comparison = (row[measurements_1] > row[preparation_2_value]) if is_high else (
            row[measurements_1] < row[preparation_2_value])
    return comparison


def get_measurements_2(result_dicts: List[Dict]) -> str:
    return result_dicts[0].get("measurements_2")


# 1-passed 2-failed 3-na 4-nottested
def process_measurements(measurements_2_str: str, df_selected: pd.DataFrame):
    measurements_2_list = measurements_2_str.splitlines()
    logging.debug("观测状态量:%s", measurements_2_list)

    code: int = 1
    msg: str = "success"
    for measurements_variable in measurements_2_list:
        measurements_2_ser = df_selected[measurements_variable]
        fifth_bits_ser = measurements_2_ser.apply(get_fifth_bit)
        fifth_bits_equal_1 = fifth_bits_ser[fifth_bits_ser == '1']
        fifth_bits_equal_1_num = len(fifth_bits_equal_1)
        logging.info("观测状态量:%s,个数:%s", measurements_variable, fifth_bits_equal_1_num)

        if fifth_bits_equal_1_num < 0:
            code = 2
            msg = f"{measurements_variable} bit4 not equal 1"
            break
    return code, msg


# ######### 数字量输出-level3,函数入口
# 1-passed 2-failed 3-na 4-not tested
def level3_debouncing_error_healing(csv_file: str, result_dicts: List[dict]):
    measurements_1: str = result_dicts[0].get("measurements_1")
    logging.info('实时观测量:%s', measurements_1)
    if not measurements_1:
        return 2, "Level1 observation 'measurements_1' not configured"

    # 观测量阈值
    preparation_2_str: str = result_dicts[0].get("preparation_2")
    if not preparation_2_str:
        return 2, "Level2: column 'preparation_2' not configured."
    preparation_2_list: list = preparation_2_str.splitlines()
    uRaw_High = preparation_2_list[0]
    uRaw_Low = preparation_2_list[1]
    logging.info('观测上限量:%s , 观测下限量:%s', uRaw_High, uRaw_Low)

    # 故障激活、触发时间表定量
    preparation_3_str: str = result_dicts[0].get("preparation_3")
    if not preparation_3_str:
        return 2, "Level3: column 'preparation_3' not configured."
    preparation_3_list: list = preparation_3_str.splitlines()
    logging.info(f"去抖时间标定量:{preparation_3_list}")

    # 故障状态量
    measurements_3_str: str = result_dicts[0].get("measurements_3")
    if not measurements_3_str:
        return 2, "Level3: column 'measurements_3' not configured."
    measurements_3_list: list = measurements_3_str.splitlines()
    logging.info("故障状态量:%s", measurements_3_list)
    if len(preparation_3_list) == 0:
        return 2, "Level3: column 'measurements_3' not configured."

    df_selected: DataFrame = pd.read_csv(csv_file, encoding='utf8')
    # 电压超上限
    upper_code, upper_msg = voltage_limit(df_selected, measurements_1, uRaw_High, 'upper', measurements_3_list)
    # 电压低下限
    lower_code, lower_msg = voltage_limit(df_selected, measurements_1, uRaw_Low, 'lower', measurements_3_list)

    ret_msg = upper_msg if upper_msg else lower_msg
    if upper_code == 1 or lower_code == 1:
        return 1, ret_msg
    elif upper_code == 2 or upper_code == 2:
        return 2, ret_msg
    elif upper_code == 0 and upper_code == 0:
        return 3, ret_msg
    elif upper_code == 4 and upper_code == 4:
        return 4, ret_msg


def voltage_limit(df_selected: DataFrame, measurements_1: str, uRaw_Limit: str, limit_type: str,
                  measurements_2_list: list[str]):
    # Define the comparison operator based on the limit type
    comp_op = operator.gt if limit_type == 'upper' else operator.lt

    # Filter the DataFrame once based on the voltage limit (超上限、低下限)
    deb_filtered_df: DataFrame = df_selected[comp_op(df_selected[measurements_1], df_selected[uRaw_Limit])]
    if len(deb_filtered_df) == 0:
        return 0, "No data exceeding the limit"

    for dfc_st_var in measurements_2_list:
        # Apply the get_fifth_bit function to the filtered DataFrame
        deb_fifth_bits_ser = deb_filtered_df[dfc_st_var].apply(get_fifth_bit)

        # Filter for rows where the fifth bit is '1'
        fault_rows = deb_filtered_df[deb_fifth_bits_ser == '1']

        if fault_rows.empty:
            return 3, "Not Found: bit4 equal 1"

        # bit4 =1 故障发生了
        # Get the last occurrence of the fault
        last_fault_row = fault_rows.iloc[-1]
        logging.info(f"故障:{dfc_st_var}，结束时间:{last_fault_row['timestamps']}")

        # Find the recovery time by looking at rows after the last fault
        ok_df_selected = df_selected[df_selected['timestamps'] > last_fault_row['timestamps']]
        if ok_df_selected.empty:
            return 2, "The failure recovery scenario was not tested"

        # Check for the first row where the fifth bit is '0'
        recovery_mask = ok_df_selected[dfc_st_var].apply(lambda x: get_third_bit(x) == '1')
        # bit4 = 0, 故障恢复了
        if recovery_mask.any():
            recovery_row = ok_df_selected[recovery_mask].iloc[0]  # Use iloc[0] to get the first match
            logging.info(f"故障: {dfc_st_var},恢复时间:{recovery_row['timestamps']}")
            return 1, "success"
        else:
            return 2, "The status of failover has not been tested"
