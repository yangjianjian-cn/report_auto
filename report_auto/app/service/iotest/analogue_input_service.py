__coding__ = "utf-8"

import logging
from typing import List

import pandas as pd

from app.service.iotest.iotest_common_service import check_row
from tools.utils.MathUtils import getBit4, getBit2, truncate_to_one_decimal_place

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# level1测试
# Level1 检查模拟量输入raw值是否改变，变量名xxx_uRawxxx
def simple_electrical_test(csv_file: str, result_dicts: List[dict]) -> str:
    # 1.数据采集
    df_selected = pd.read_csv(csv_file, encoding='utf8')

    # 2.数据清洗
    # 填充 NaN 值为 0
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"实时电压:{uRaw}")

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
def high_error_detection(csv_file: str, result_dicts) -> tuple:
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    df_selected['is_level2_high'] = df_selected.apply(lambda row: check_row(row, result_dicts, True), axis=1)
    high_passed_count = (df_selected['is_level2_high'] == 'passed').sum()
    high_level2 = 'passed' if high_passed_count > 0 else 'failed'
    return high_level2


# level2测试
def low_error_detection(csv_file: str, result_dicts) -> tuple:
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    df_selected['is_level2_low'] = df_selected.apply(lambda row: check_row(row, result_dicts, False), axis=1)
    low_passed_count = (df_selected['is_level2_low'] == 'passed').sum()
    low_level2 = 'passed' if low_passed_count > 0 else 'failed'
    return low_level2


# level3测试
def high_error_debouncing_error_healing(csv_file, result_dicts):
    measurements_1: str = result_dicts[0].get("measurements_1")
    preparation_2_str: str = result_dicts[0].get("preparation_2")

    preparation_3_str: str = result_dicts[0].get("preparation_3")
    measurements_3_str: str = result_dicts[0].get("measurements_3")
    logging.info('测量值:%s', measurements_1)

    # 阈值
    preparation_2_list: list = preparation_2_str.splitlines()
    uRaw_High = preparation_2_list[0]
    logging.info('阈值上限:%s', uRaw_High)

    # 故障激活、触发时间
    preparation_2_list: list = preparation_3_str.splitlines()
    max_deb_def_str: str = preparation_2_list[0]
    max_deb_ok_str: str = preparation_2_list[1]
    logging.info('超上限故障激活时间:%s', max_deb_def_str)
    logging.info('超上限故障恢复时间:%s', max_deb_ok_str)

    # DFC异常值
    measurements_2_list: list = measurements_3_str.splitlines()
    dfc_max_str: str = measurements_2_list[0]
    logging.info("高电平状态:%s", dfc_max_str)

    # ①电压超过上限-触发故障
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    filtered_df = df_selected[(df_selected[measurements_1] > df_selected[uRaw_High])]

    high_deb_level3 = 'failed'
    high_ok_level3 = 'failed'
    bit4_last_row_timestamps = 0
    if len(filtered_df) != 0:
        # bit2= 1 ,故障触发,激活时间
        filtered_df_bit2 = filtered_df[(filtered_df[dfc_max_str].apply(getBit2) == '1')]
        if len(filtered_df_bit2) != 0:
            # 故障激活
            bit2_begin_row_timestamps = filtered_df_bit2.iloc[0]['timestamps']
            max_deb_def_f = filtered_df_bit2.iloc[0][max_deb_def_str]
            max_deb_def_f = max_deb_def_f / 1000
            bit2_end_row_timestamps = bit2_begin_row_timestamps + max_deb_def_f
            logging.info(f"故障激活:{bit2_begin_row_timestamps} - {bit2_end_row_timestamps} ")

            # 故障发生
            filtered_df_bit4 = filtered_df[
                (filtered_df['timestamps'] > bit2_end_row_timestamps) & (
                        filtered_df[dfc_max_str].apply(getBit4) == '1')]
            if not filtered_df_bit4.empty:
                high_deb_level3 = 'passed'
                bit4_last_row_timestamps = filtered_df_bit4.iloc[-1]['timestamps']
                logging.info(f"故障结束:{bit4_last_row_timestamps}")

    # 电压超过上限-故障恢复
    filtered_df = df_selected[(df_selected['timestamps'] > bit4_last_row_timestamps)]
    if len(filtered_df) != 0:
        filtered_df = filtered_df[(filtered_df[measurements_1] < filtered_df[uRaw_High])]  # 电压降下来了
        filtered_df_bit2 = filtered_df[(filtered_df[dfc_max_str].apply(getBit2) == '1')]
        if len(filtered_df_bit2) != 0:
            # 故障激活
            bit2_begin_row_timestamps = filtered_df_bit2.iloc[0]['timestamps']
            max_deb_ok_f = filtered_df_bit2.iloc[0][max_deb_ok_str]
            max_deb_ok_f = max_deb_ok_f / 1000
            bit2_end_row_timestamps = bit2_begin_row_timestamps + max_deb_ok_f
            logging.info(f"电压超上限-恢复时间:{bit2_begin_row_timestamps} - {bit2_end_row_timestamps} ")

            filtered_df_bit4 = filtered_df[filtered_df['timestamps'] > bit2_end_row_timestamps]
            if len(filtered_df_bit4) != 0:
                dfc_max_series = filtered_df_bit4[dfc_max_str]
                dfc_max_series_unique_values: list = dfc_max_series.unique()
                for value in dfc_max_series_unique_values:
                    if getBit4(value) == '0':
                        high_ok_level3 = 'passed'

    return high_deb_level3, high_ok_level3


def low_error_debouncing_error_healing(csv_file, result_dicts):
    logging.info(f"file:{csv_file}")
    measurements_1: str = result_dicts[0].get("measurements_1")
    preparation_2_str: str = result_dicts[0].get("preparation_2")

    preparation_3_str: str = result_dicts[0].get("preparation_3")
    measurements_3_str: str = result_dicts[0].get("measurements_3")

    logging.info('测量值:%s', measurements_1)

    # 阈值
    preparation_2_list: list = preparation_2_str.splitlines()
    uRaw_Low = preparation_2_list[1]
    logging.info('阈值下限:%s', uRaw_Low)

    # 故障激活、触发时间
    preparation_2_list: list = preparation_3_str.splitlines()
    min_deb_def_str: str = preparation_2_list[2]
    min_deb_ok_str: str = preparation_2_list[3]
    logging.info('低下限故障激活:%s', min_deb_def_str)
    logging.info('低下限故障恢复:%s', min_deb_ok_str)

    # DFC异常值
    measurements_2_list: list = measurements_3_str.splitlines()
    dfc_min_var: str = measurements_2_list[1]
    logging.info("低电平状态:%s", dfc_min_var)

    low_deb_level3 = 'failed'
    low_ok_level3 = 'failed'
    bit4_last_row_timestamps: float = 0
    # ② 电压低于下限-触发故障
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    filtered_df = df_selected[(df_selected[measurements_1] < df_selected[uRaw_Low])]
    if len(filtered_df) != 0:  # 存在
        # bit2= 1 ,故障触发,激活时间
        filtered_df_bit2 = filtered_df[(filtered_df[dfc_min_var].apply(getBit2) == '1')]
        if len(filtered_df_bit2) != 0:
            # 开始激活
            bit2_begin_row_timestamps = filtered_df_bit2.iloc[0]['timestamps']
            min_deb_def_f = filtered_df_bit2.iloc[0][min_deb_def_str]
            min_deb_def_f = min_deb_def_f / 1000
            bit2_end_row_timestamps = bit2_begin_row_timestamps + min_deb_def_f
            logging.info(f"电压低于下限-故障激活时间:{bit2_begin_row_timestamps} - {bit2_end_row_timestamps} ")

            # 故障触发
            filtered_df_bit4 = filtered_df[(filtered_df['timestamps'] > bit2_end_row_timestamps) & (
                    filtered_df[dfc_min_var].apply(getBit4) == '1')]
            if not filtered_df_bit4.empty:
                low_deb_level3 = 'passed'
                bit4_last_row_timestamps = filtered_df_bit4.iloc[-1]['timestamps']
                logging.info(f"故障结束时间:{bit4_last_row_timestamps}")

    if bit4_last_row_timestamps == 0:
        return "", ""

    # 电压低于下限-故障恢复
    filtered_df = df_selected[(df_selected['timestamps'] > bit4_last_row_timestamps)]
    if len(filtered_df) != 0:
        filtered_df = filtered_df[(filtered_df[measurements_1] > filtered_df[uRaw_Low])]  # 电压恢复
        filtered_df_bit2 = filtered_df[(filtered_df[dfc_min_var].apply(getBit2) == '1')]
        if len(filtered_df_bit2) != 0:
            # 故障恢复-激活时间
            bit2_begin_row_timestamps = filtered_df_bit2.iloc[0]['timestamps']
            min_deb_ok_f = filtered_df_bit2.iloc[0][min_deb_ok_str]
            min_deb_ok_f = min_deb_ok_f / 1000
            bit2_end_row_timestamps = bit2_begin_row_timestamps + min_deb_ok_f
            logging.info(f"低于下限-故障恢复时间:{bit2_begin_row_timestamps} - {bit2_end_row_timestamps} ")

            filtered_df_bit4 = filtered_df[filtered_df['timestamps'] > bit2_end_row_timestamps]
            if len(filtered_df_bit4) != 0:
                dfc_mix_series = filtered_df_bit4[dfc_min_var]
                dfc_mix_series_unique_values: list = dfc_mix_series.unique()
                for value in dfc_mix_series_unique_values:
                    if getBit4(value) == '0':
                        low_ok_level3 = 'passed'

    return low_deb_level3, low_ok_level3


# level4测试
def high_substitute_value_reaction_test(csv_file: str, result_dicts) -> str:
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    uRaw = result_dicts[0].get("measurements_1")
    logging.info(f"测量电压:{uRaw}")

    preparation_2_str: str = result_dicts[0].get("preparation_2")
    preparation_2_list: list = preparation_2_str.splitlines()
    uRawHigh: str = preparation_2_list[0]
    logging.info(f"电压上限:{uRawHigh}")

    preparation_2_str: str = result_dicts[0].get("measurements_4")
    logging.info(f"观测电压:{preparation_2_str}")

    uRaw1Def: str = result_dicts[0].get("preparation_4")
    logging.info(f"默认电压:{uRaw1Def}")

    high_level4 = "failed"
    # raw值超上限时，检查目标值是否被default值替代
    filtered_df = df_selected[df_selected[uRaw] > df_selected[uRawHigh]]
    if len(filtered_df) != 0:
        # 检查 'APP_uRaw1' 和 'APP_uRaw1Def_C' 是否完全相等
        equal_values = filtered_df[filtered_df[preparation_2_str] == filtered_df[uRaw1Def]]
        if not equal_values.empty:
            high_level4 = "passed"
    return high_level4
