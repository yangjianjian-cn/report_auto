__coding__ = "utf-8"

import logging
from typing import List

import pandas as pd

from tools.utils.MathUtils import truncate_to_one_decimal_place

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# level1测试
# Level1 检查模拟量输入raw值是否改变，变量名xxx_uRawxxx
# 1-passed 2-failed 3-na 4-nottested
def simple_electrical_test(csv_file: str, result_dicts: List[dict]) -> str:
    # 1.数据采集
    df_selected = pd.read_csv(csv_file, encoding='utf8')

    # 2.数据清洗
    # 填充 NaN 值为 0
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"level1 观测电压量:{uRaw}")

    df_selected[uRaw] = df_selected[uRaw].fillna(0)
    # 选择 'APP_uRaw1unLim'列，并对每个元素执行除以 1000 取整的操作
    result_set = set(df_selected[uRaw].apply(truncate_to_one_decimal_place))
    if len(result_set) == 0:
        return 3, 'n/a'

    # 3.数据计算
    # 过滤掉 0 和 5
    filtered_set = {value for value in result_set if value not in [0, 5]}
    element_count = len(filtered_set)
    logging.info(f"level1 观测电压的取值个数:{element_count}")

    if element_count > 0:
        code, msg = 1, 'passed'
    else:
        code, msg = 2, 'failed'
    return code, msg


# level4测试
# 1-passed 2-failed 3-na 4-nottested
def substitute_value_reaction_test(csv_file: str, result_dicts, test_type: str) -> str:
    # 通用部分
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"level1测量电压:{uRaw}")
    if not uRaw:
        return 2, "level1 column 'measurements_1' not configured"

    # level2 preparation_2,电压阈值
    preparation_2_str: str = result_dicts[0].get("preparation_2")
    if not preparation_2_str:
        return 2, " level2 column 'preparation_2' not configured"
    preparation_2_list: list = preparation_2_str.splitlines()
    if len(preparation_2_list) != 2:
        return 2, " level2 column 'preparation_2' configured error"
    uRawLimit: str = preparation_2_list[0 if test_type == 'high' else 1]
    logging.info(f"{'电压上限' if test_type == 'high' else '电压下限'}:{uRawLimit}")

    # level4 preparation_4 默认电压
    uRaw1Def: str = result_dicts[0].get("preparation_4")
    logging.info(f"默认电压:{uRaw1Def}")
    if not uRaw1Def:
        return 2, "level4 column preparation_4 not configured(Default voltage value)"

    # level4 measurements_4 实际观测电压
    observed_voltage: str = result_dicts[0].get("measurements_4")
    logging.info(f"level4 column 'measurements_4':{observed_voltage}")
    if not observed_voltage:
        return 2, "level4 column measurements_4 not configured"

    # 根据test_type决定是检查上限还是下限
    if test_type == 'high':
        filtered_df = df_selected[df_selected[observed_voltage] > df_selected[uRawLimit]]
    elif test_type == 'low':
        filtered_df = df_selected[df_selected[observed_voltage] < df_selected[uRawLimit]]

    test_rslt = 3, "n/a"
    if not filtered_df.empty:
        # 检查 'APP_uRaw1' 和 'APP_uRaw1Def_C' 是否完全相等
        equal_values = filtered_df[filtered_df[observed_voltage] == filtered_df[uRaw1Def]]
        if not equal_values.empty:
            test_rslt = 1, "passed"
    return test_rslt


def analogue_input_level4(csv_file: str, result_dicts) -> dict:
    results = {
        'high': substitute_value_reaction_test(csv_file, result_dicts, "high"),
        'low': substitute_value_reaction_test(csv_file, result_dicts, "low")
    }

    results_high_code, results_high_msg = results['high']
    results_low_code, results_low_msg = results['low']

    # 如果需要日志记录，可以在下面添加
    logging.info(f"Level4 High Test Result: {results_high_code},{results_high_msg}")
    logging.info(f"Level4 Low Test Result: {results_low_code},{results_low_msg}")

    if results_high_code == 1 or results_low_code == 1:
        return 1, "success"
    elif results_high_code == 2 or results_low_code == 2:
        return 2, "failure"
    elif results_high_code == 3 and results_low_code == 3:
        results_msg = results_high_msg if results_high_msg else results_low_msg
        return 3, results_msg
    elif results_high_code == 4 and results_low_code == 4:
        results_msg = results_high_msg if results_high_msg else results_low_msg
        return 4, results_msg
