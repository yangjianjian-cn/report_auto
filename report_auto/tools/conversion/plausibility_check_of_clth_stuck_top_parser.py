__coding__ = "utf-8"

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from constant.faultType import FAULT_TYPE_MAPPING
from constant.replacements import plausibility_check_of_clth_stuck_top_replacements
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.csv_column_rename import find_columns_with_dfc_err_type
from tools.common.report_common import ret_fault_detection
from tools.report.report_generation import replace_variables_in_doc
from tools.utils.MathUtils import getBit0

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def plausibility_check_of_clth_stuck_top(req_data: ReqPOJO):
    df_selected = pd.read_csv(req_data.csv_path, encoding='utf8')

    # 设备初始化
    err_msg, replacements, draw_detection_figure_df = initial_state(df_selected)
    if len(err_msg) > 0:
        # 初始化失败
        draw_graph(draw_detection_figure_df, req_data, replacements)
        return err_msg

    # 设备初始化成功，故障检测
    err_msg, replacements, draw_fault_detection_df = fault_detection(draw_detection_figure_df)
    if len(err_msg) > 0:
        # 检测出现异常
        draw_graph(draw_fault_detection_df, req_data, replacements)
        return err_msg

    # 检测通过
    output_path = draw_graph(draw_fault_detection_df, req_data, replacements)
    err_msg.append(f"succeed:{output_path}")
    return err_msg


def initial_state(df_selected: DataFrame):
    err_msg = []
    replacements = {}

    # 1. Enter initial state
    # CoEng_st = COENG_RUNNING
    begin_time = df_selected.iloc[0]['timestamps']
    condition1 = df_selected['CoEng_st'] == 'COENG_RUNNING'
    initial_state_df_1 = df_selected[condition1]
    if len(initial_state_df_1) == 0:
        err_msg.append('initial state CoEng_st=COENG_RUNNING  failure ')
        replacements = plausibility_check_of_clth_stuck_top_replacements(is_fail='❌ ')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, df_selected)

    # VehV_v > 0
    begin_time = initial_state_df_1.iloc[0]['timestamps']
    condition2 = initial_state_df_1['VehV_v'] > 0
    initial_state_df_2 = initial_state_df_1[condition2]
    if len(initial_state_df_2) == 0:
        err_msg.append('initial state VehV_v > 0  failure ')
        replacements = plausibility_check_of_clth_stuck_top_replacements(is_fail='❌ ')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, initial_state_df_1)

    return err_msg, replacements, initial_state_df_2


def fault_detection(initial_state_df: DataFrame):
    err_msg = []
    fault_detection_df = initial_state_df.copy()
    begin_time = fault_detection_df.iloc[0]['timestamps']

    # 1.Tra_numGear != Clth_numLastVldGear
    condition2 = fault_detection_df['Tra_numGear'] != fault_detection_df['Clth_numLastVldGear']
    fault_detection_df_2 = fault_detection_df[condition2]
    if len(fault_detection_df_2) == 0:
        err_msg.append('fault detection Tra_numGear != Clth_numLastVldGear failure ')
        replacements = plausibility_check_of_clth_stuck_top_replacements(is_fail='❌ ', is_not_equ='❌ ')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, fault_detection_df)

    # 2. Fault detection
    # Clth_st.0=0
    fault_detection_df.loc[:, 'clth_st_bit0'] = fault_detection_df['Clth_st'].apply(getBit0)
    condition3 = fault_detection_df['clth_st_bit0'] == '0'
    fault_detection_df_3 = fault_detection_df[condition3]
    if len(fault_detection_df_3) == 0:
        err_msg.append('fault detection  Clth_st.0 = 0 failure ')
        replacements = plausibility_check_of_clth_stuck_top_replacements(is_fail='❌ ', clth_st_0='❌ ', is_not_equ='√')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, fault_detection_df)

    #  3. DFC_ClthNplOpn is set
    begin_time = fault_detection_df_3.iloc[0]['timestamps']
    err_type: str = FAULT_TYPE_MAPPING.get('plausibility_check_of_clth_stuck_top')
    signals_dfes = find_columns_with_dfc_err_type(fault_detection_df_3, err_type)
    if len(signals_dfes) == 0:
        err_msg.append(f"fault detection {err_type} is set  failure:{len(fault_detection_df)}")
        replacements = plausibility_check_of_clth_stuck_top_replacements(is_fail='❌ ', clth_st_0='√', is_not_equ='√',
                                                                         dfc_clthnplopn='❌ ')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, fault_detection_df_3)

    condition4 = fault_detection_df_3[signals_dfes[0]] == err_type
    fault_detection_df_4 = fault_detection_df_3[condition4]
    end_time = fault_detection_df_4.iloc[-1]['timestamps']
    replacements = plausibility_check_of_clth_stuck_top_replacements(is_pass='√', clth_st_0='√', is_not_equ='√',dfc_clthnplopn='√')
    return ret_fault_detection(end_time, begin_time, replacements, err_msg, fault_detection_df_3)


def draw_graph(draw_fault_detection_df: DataFrame, req_data: ReqPOJO, replacements: map):
    logging.info(f"模板参数:{replacements}")

    signals = ['VehV_v', 'Clth_st', 'Tra_numGear', 'Clth_numLastVldGear']
    logging.info(f"信号列:{signals}")

    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name
    logging.info(f"输出文件名:{output_name}")

    output_path = replace_variables_in_doc(replacements, draw_fault_detection_df, signals, req_data)
    return output_path
