import logging
from typing import List

import pandas as pd

from tools.utils.MathUtils import getBit4, truncate_to_one_decimal_place

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def check_row(row, result_dicts: dict):
    measurements_1 = result_dicts[0].get("measurements_1")
    preparation_2 = result_dicts[0].get("preparation_2")
    measurements_2 = result_dicts[0].get("measurements_2")
    logging.info(f"measurements_1: {measurements_1}, preparation_2:{preparation_2}, measurements_2: {measurements_2}")

    if row['APP_uRaw1unLim'] > row['APP_uRaw1SRCHigh_C']:  # 电压 > 上限电压
        return 'passed' if getBit4(row['DFC_st.DFC_SRCHighAPP1']) == '1' else 'failed'
    elif row['APP_uRaw1unLim'] < row['APP_uRaw1SRCLow_C']:  # 电压 < 下限电压
        return 'passed' if getBit4(row['DFC_st.DFC_SRCLowAPP1']) == '1' else 'failed'


# level1测试
# Level1 检查模拟量输入raw值是否改变，变量名xxx_uRawxxx
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
# raw值大于上限、raw值小于下限
def error_detection(csv_file: str, result_dicts) -> str:
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    df_selected['is_level2'] = df_selected.apply(lambda row: check_row(row, result_dicts), axis=1)
    passed_count = (df_selected['is_level2'] == 'passed').sum()
    if passed_count > 0:
        level2 = 'passed'
    else:
        level2 = 'failed'
    return level2


# level3测试
def error_debouncing_error_healing(csv_file, result_dicts):
    # 电压超过上限-触发故障
    bit4_last_row_timestamps = 0
    df_selected = pd.read_csv(csv_file, encoding='utf8')
    filtered_df = df_selected[(df_selected['APP_uRaw1unLim'] > df_selected['APP_uRaw1SRCHigh_C'])]
    if len(filtered_df) != 0:
        # bit2= 1 激活，故障触发
        filtered_df_bit2 = filtered_df[(filtered_df['DFC_st.DFC_SRCHighAPP1'].apply(getBit2) == '1')]
        if len(filtered_df_bit2) != 0:
            # 最后激活时间
            bit2_last_row_timestamps = filtered_df_bit2.iloc[-1]['timestamps']
            logging.info(f"故障激活时间:{bit2_last_row_timestamps}")
            # 故障发生了
            filtered_df_bit4 = filtered_df[(filtered_df['timestamps'] > bit2_last_row_timestamps) & (
                    filtered_df['DFC_st.DFC_SRCHighAPP1'].apply(getBit4) == '1')]
            if filtered_df_bit4.empty:
                level3 = 'failed'
            else:
                # 最后故障时间
                level3 = 'passed'
                bit4_last_row_timestamps = filtered_df_bit4.iloc[-1]['timestamps']
                logging.info(f"故障结束时间:{bit4_last_row_timestamps}")

    # 电压超过上限-故障恢复
    filtered_df = df_selected[(df_selected['timestamps'] > bit4_last_row_timestamps)]
    if len(filtered_df) != 0:
        # 故障恢复激活中
        filtered_df_bit2 = filtered_df[(filtered_df['DFC_st.DFC_SRCHighAPP1'].apply(getBit2) == '1')]
        if len(filtered_df_bit2) != 0:
            # 故障恢复-激活-结束时间
            bit2_last_row_timestamps = filtered_df_bit2.iloc[-1]['timestamps']
            logging.info(f"故障恢复时间:{bit2_last_row_timestamps}")

            filtered_df_bit4 = filtered_df[filtered_df['timestamps'] > bit2_last_row_timestamps]
            if len(filtered_df_bit4) != 0:
                filtered_df_bit4 = filtered_df_bit4.head(1)
                if getBit4(filtered_df_bit4['DFC_st.DFC_SRCHighAPP1']) == '0':
                    level3 = 'passed'
                else:
                    level3 = 'failed'


# level4测试
def substitute_value_reaction_test(csv_file:str, result_dicts)->str:
    df_selected = pd.read_csv(csv_file, encoding='utf8')

    # raw值超限时，检查目标值是否被default值替代
    filtered_df = df_selected[df_selected['APP_uRaw1unLim'] > df_selected['APP_uRaw1SRCHigh_C']]
    filtered_df = filtered_df[filtered_df['DFC_st.DFC_SRCHighAPP1'].apply(getBit4) == '1']
    if len(filtered_df) != 0:
        # 检查 'APP_uRaw1' 和 'APP_uRaw1Def_C' 是否完全相等
        are_equal = (filtered_df['APP_uRaw1'] == filtered_df['APP_uRaw1Def_C']).all()
    if are_equal:
        level4 = "passed"
    else:
        level4 = "failed"
    return level4
