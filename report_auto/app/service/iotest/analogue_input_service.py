__coding__ = "utf-8"

import logging
from typing import List

import pandas as pd

from tools.utils.MathUtils import scale_and_truncate

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
    logging.info(f"level1 观测电压label:{uRaw}")

    df_selected[uRaw] = df_selected[uRaw].fillna(0)
    # 选择 'APP_uRaw1unLim'列，并对每个元素执行除以 1000 取整的操作

    uRaw_max = df_selected[uRaw].max()
    result_set = set(df_selected[uRaw].apply(lambda x: scale_and_truncate(x, uRaw_max)))
    print(result_set)
    if len(result_set) == 0:
        return 3, 'n/a'

    # 3.数据计算
    # 过滤掉 0 和 5
    filtered_set = {value for value in result_set if value not in [0, 5]}
    element_count = len(filtered_set)
    logging.info(f"level1 观测电压取值个数:{element_count}")

    if element_count > 0:
        code, msg = 1, 'passed'
    else:
        code, msg = 2, 'The number of voltage jumps does not match'
    return code, msg


# level4测试
# 1-passed 2-failed 3-na 4-nottested
def substitute_value_reaction_test(csv_file: str, result_dicts: list, test_type: str) -> tuple:
    # Load the CSV file into a DataFrame
    try:
        df = pd.read_csv(csv_file, encoding='utf8')
    except Exception as e:
        logging.error(f"Failed to read CSV file {csv_file}: {e}")
        return 2, "Failed to read CSV file"

    # Extract and validate the necessary parameters from result_dicts
    def get_param(key, error_msg):
        value = result_dicts[0].get(key)
        if not value:
            logging.error(error_msg)
            return None, (3, error_msg)
        return value, None

    # 实时观测电压
    uRaw, err = get_param("measurements_1", "level1 column 'measurements_1' not configured")
    if err: return err

    # 电压阈值
    preparation_2_str, err = get_param("preparation_2", "level2 column 'preparation_2' not configured")
    if err: return err

    # 观测结果
    observed_voltage, err = get_param("measurements_4", "level4 column measurements_4 not configured")
    if err: return err

    # 默认电压
    uRaw1Def, err = get_param("preparation_4", "level4 column preparation_4 not configured(Default voltage value)")
    if err: return err

    # 电压阈值，数量校验：Parse the preparation_2 string into a limit for comparison
    preparation_2_list = preparation_2_str.splitlines()
    if len(preparation_2_list) != 2:
        logging.error("level2 column 'preparation_2' configured error")
        return 2, "level2 column 'preparation_2' configured error"

    # 电压阈值(Series)
    uRawLimit = preparation_2_list[0 if test_type == 'high' else 1]
    logging.info(f"{'电压上限' if test_type == 'high' else '电压下限'}: {uRawLimit}")

    # Convert the default voltage string into a list of floats
    uRaw1Def_list = uRaw1Def.splitlines()
    logging.info(f"默认电压: {uRaw1Def_list}")

    # Perform the test based on the test type
    try:
        # Ensure that the columns exist in the DataFrame
        if uRaw not in df.columns or observed_voltage not in df.columns:
            raise KeyError("Required columns are missing from the CSV file")

        # Filter the DataFrame based on the test type
        condition = df[uRaw] > df[uRawLimit] if test_type == 'high' else df[uRaw] < df[uRawLimit]
        filtered_df = df[condition]

        # If no rows match the condition, return a failure message
        if filtered_df.empty:
            return 3, f"No {test_type} voltage exceed limit found"

        # Check if any of the observed voltages match the default values
        rslt4 = 2, " Default value not set "  # If none of the default voltages matched, return a failure message
        for one_uRaw1Def in uRaw1Def_list:
            equal_values_df = \
                filtered_df[
                    filtered_df[observed_voltage].astype(float).round() == filtered_df[one_uRaw1Def].astype(float).round()
                ]
            if not equal_values_df.empty:
                rslt4 = 1, "passed"
        return rslt4
    except Exception as e:
        logging.error(f"An error occurred during the test: {e}")
        return 2, "An error occurred during the test"


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
