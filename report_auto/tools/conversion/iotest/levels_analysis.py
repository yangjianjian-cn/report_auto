import logging
from typing import List

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# pwm输入-level1
def pwm_simple_electrical_test(csv_file: str, result_dicts: List[dict]) -> str:
    # 1.数据采集
    df_selected = pd.read_csv(csv_file, encoding='utf8')

    # 2.数据清洗
    # 填充 NaN 值为 0
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"实时电压:{uRaw}")

    # 四舍五入到最近的整数
    rounded_values = set(df_selected[uRaw].round().astype(int))
    if len(rounded_values) > 0:
        level1 = 'passed'
    else:
        level1 = 'failed'
    return level1


# 数字输入-level1
def digital_simple_electrical_test(csv_file: str, result_dicts: List[dict]) -> str:
    # 1.数据采集
    df_selected = pd.read_csv(csv_file, encoding='utf8')

    # 2.数据清洗
    # 填充 NaN 值为 0
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"实时电压:{uRaw}")

    df_selected[uRaw] = df_selected[uRaw].fillna(0)
    result_set = set(df_selected[uRaw])
    element_count = len(result_set)

    if element_count > 0:
        level1 = 'passed'
    else:
        level1 = 'failed'
    return level1


def low_substitute_value_reaction_test(csv_file: str, result_dicts) -> str:
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"测量电压:{uRaw}")

    preparation_2_str: str = result_dicts[0].get("preparation_2")
    preparation_2_list: list = preparation_2_str.splitlines()
    uRawLow: str = preparation_2_list[1]
    logging.info(f"电压下限:{uRawLow}")

    preparation_2_str: str = result_dicts[0].get("measurements_4")
    logging.info(f"观测电压:{preparation_2_str}")

    uRaw1Def: str = result_dicts[0].get("preparation_4")
    logging.info(f"默认电压:{uRaw1Def}")

    low_level4 = "failed"
    # raw值低下限时，检查目标值是否被default值替代
    filtered_df = df_selected[df_selected[uRaw] < df_selected[uRawLow]]
    if len(filtered_df) != 0:
        # 检查 'APP_uRaw1' 和 'APP_uRaw1Def_C' 是否完全相等
        equal_values = filtered_df[filtered_df[preparation_2_str] == filtered_df[uRaw1Def]]
        if not equal_values.empty:
            low_level4 = "passed"

    return low_level4
