import logging
from typing import List

import pandas as pd

from tools.utils.MathUtils import getBit4, truncate_to_one_decimal_place

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def check_row(row, result_dicts: dict):
    measurements_1 = result_dicts[0].get("measurements_1")
    measurements_2 = result_dicts[0].get("measurements_2")
    logging.info(f"measurements_1: {measurements_1}, measurements_2: {measurements_2}")

    if row['APP_uRaw1unLim'] > row['APP_uRaw1SRCHigh_C']:  # 电压 > 上限电压
        return 'passed' if getBit4(row['DFC_st.DFC_SRCHighAPP1']) == '1' else 'failed'
    elif row['APP_uRaw1unLim'] < row['APP_uRaw1SRCLow_C']:  # 电压 < 下限电压
        return 'passed' if getBit4(row['DFC_st.DFC_SRCLowAPP1']) == '1' else 'failed'


# level1测试
def simple_electrical_test(csv_file: str, result_dicts: List[dict]) -> str:
    # 1.数据采集
    df_selected = pd.read_csv(csv_file, encoding='utf8')

    # 2.数据清洗
    # 填充 NaN 值为 0
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"measurement variable:{uRaw}")

    df_selected[uRaw] = df_selected[uRaw].fillna(0)
    # 选择 'APP_uRaw1unLim'列，并对每个元素执行除以 1000 取整的操作
    result_set = set(df_selected[uRaw].apply(truncate_to_one_decimal_place))

    # 3.数据计算
    # 过滤掉 0 和 5
    filtered_set = {value for value in result_set if value not in [0, 5]}
    element_count = len(filtered_set)
    if element_count > 0:
        level1 = 'passed'
    else:
        level1 = 'failed'
    return level1


# level2测试
def error_detection(csv_file: str, result_dicts):
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    df_selected['is_level2'] = df_selected.apply(lambda row: check_row(row, result_dicts), axis=1)
    passed_count = (df_selected['is_level2'] == 'passed').sum()
    if passed_count > 0:
        level2 = 'passed'
    else:
        level2 = 'failed'
