__coding__ = "utf-8"

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from constant.faultType import FAULT_TYPE_MAPPING
from constant.replacements import plausibility_check_of_clth_stuck_bottom_replacements
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.csv_column_rename import find_columns_with_dfc_err_type
from tools.common.report_common import ret_fault_detection
from tools.report.report_generation import replace_variables_in_doc
from tools.utils.MathUtils import getBit0

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def plausibility_check_of_clth_stuck_bottom(req_data: ReqPOJO):
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
    begin_time = df_selected.iloc[0]['timestamps']

    condition1 = df_selected['CoEng_st'] == 'COENG_RUNNING'
    initial_state_df_1 = df_selected[condition1]
    if len(initial_state_df_1) == 0:
        err_msg.append("initial state CoEng_st = COENG_RUNNING failure")
        replacements = plausibility_check_of_clth_stuck_bottom_replacements(is_fail='√')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, df_selected)

    begin_time = initial_state_df_1.iloc[0]['timestamps']
    condition2 = initial_state_df_1['VehV_v'] > 0
    initial_state_df_2 = initial_state_df_1[condition2]
    if len(initial_state_df_2) == 0:
        err_msg.append("initial state VehV_v > 0 failure")
        replacements = plausibility_check_of_clth_stuck_bottom_replacements(is_fail='√')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, initial_state_df_1)

    return err_msg, replacements, initial_state_df_2


def fault_detection(initial_state_df: DataFrame):
    err_msg = []
    fault_detection_df = initial_state_df.copy()

    # 2. Fault detection
    begin_time = fault_detection_df.iloc[0]['timestamps']
    g_begin_time = fault_detection_df.iloc[0]['timestamps']

    fault_detection_df.loc[:, 'clth_st_bit0'] = fault_detection_df['Clth_st'].apply(getBit0)
    condition3 = fault_detection_df['clth_st_bit0'] == '0'
    fault_detection_df_3 = fault_detection_df[condition3]
    if len(fault_detection_df_3) == 0:
        err_msg.append(f"fault detection Clth_st.0 =0 failure")
        replacements = plausibility_check_of_clth_stuck_bottom_replacements(is_fail='√', clth_st_0='❌ ')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, fault_detection_df)

    begin_time = fault_detection_df_3.iloc[0]['timestamps']
    condition4 = fault_detection_df_3['Clth_bAutoStrtEnaCond'] == 1
    fault_detection_df_4 = fault_detection_df_3[condition4]
    if len(fault_detection_df_4) == 0:
        err_msg.append("fault detection Clth_bAutoStrtEnaCond=1 failure")
        replacements = plausibility_check_of_clth_stuck_bottom_replacements(is_fail='√', clth_st_0='√',
                                                                            clth_bautostrtenacond='❌ ')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, fault_detection_df)

    begin_time = fault_detection_df_4.iloc[0]['timestamps']
    condition5 = fault_detection_df_4['Tra_numGear'] != fault_detection_df_4['Clth_numLastVldGear']
    fault_detection_df_5 = fault_detection_df_4[condition5]
    if len(fault_detection_df_5) == 0:
        err_msg.append("fault detection  Tra_numGear!=Clth_numLastVldGear failure")
        replacements = plausibility_check_of_clth_stuck_bottom_replacements(is_fail='√', clth_st_0='√',
                                                                            clth_bautostrtenacond='√', is_not_equ='❌ ')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, fault_detection_df)

    begin_time = fault_detection_df_5.iloc[0]['timestamps']
    condition6 = fault_detection_df_5['Clth_bClthPlausErr'] == 1
    fault_detection_df_6 = fault_detection_df_5[condition6]
    if len(fault_detection_df_6) == 0:
        err_msg.append("fault detection Clth_bClthPlausErr=1 failure")
        replacements = plausibility_check_of_clth_stuck_bottom_replacements(is_fail='√', clth_st_0='√',
                                                                            clth_bautostrtenacond='√', is_not_equ='√',
                                                                            clth_bclthplauserr='❌ ')
        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, fault_detection_df)

        #  DFC_ClthNplOpn is set
    err_type: str = FAULT_TYPE_MAPPING.get('plausibility_check_of_clth_stuck_bottom')
    signals_dfes = find_columns_with_dfc_err_type(fault_detection_df_6, err_type)
    if len(signals_dfes) == 0:
        err_msg.append(f"fault detection {err_type} is set  failure")
        replacements = plausibility_check_of_clth_stuck_bottom_replacements(is_fail='√', clth_st_0='√',
                                                                            clth_bautostrtenacond='√', is_not_equ='√',
                                                                            clth_bclthplauserr='√',
                                                                            dfc_clthplauschk='❌ ')

        return ret_fault_detection(begin_time + 5, begin_time, replacements, err_msg, fault_detection_df)

    condition7 = fault_detection_df_6[signals_dfes[0]] == err_type
    fault_detection_df_7 = fault_detection_df_6[condition7]
    end_time = fault_detection_df_7.iloc[-1]['timestamps']
    replacements = plausibility_check_of_clth_stuck_bottom_replacements(is_pass='√', clth_st_0='√',
                                                                        clth_bautostrtenacond='√', is_not_equ='√',
                                                                        clth_bclthplauserr='√', dfc_clthplauschk='√')
    return ret_fault_detection(end_time, g_begin_time, replacements, err_msg, fault_detection_df)


def draw_graph(draw_fault_detection_df: DataFrame, req_data: ReqPOJO, replacements: map):
    logging.info(f"模板参数:{replacements}")

    signals = ['VehV_v', 'Clth_st', 'Clth_bAutoStrtEnaCond', 'Tra_numGear', 'Clth_numLastVldGear',
               'Clth_bClthPlausErr', 'DFC_st.DFC_ClthPlausChk']
    logging.info(f"信号量:{signals}")

    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name
    logging.info(f"输出文件名:{output_name}")

    output_path = replace_variables_in_doc(replacements, draw_fault_detection_df, signals, req_data)
    return output_path
