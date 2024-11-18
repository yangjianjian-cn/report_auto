__coding__ = "utf-8"

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from constant.faultType import FAULT_TYPE_MAPPING
from constant.replacements import main_brake_plausibility_check_replacements
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.csv_column_rename import err_type_contains_strings, find_columns_with_dfc_err_type
from tools.common.report_common import ret_fault_detection
from tools.report.report_generation import replace_variables_in_doc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def brake_plausibility_check(req_data: ReqPOJO, brkStMn: bool, brkStRed: bool, tplt_type: str):
    df_selected = pd.read_csv(req_data.csv_path, encoding='utf8')

    # 设备初始化
    err_msg, replacements, draw_fault_detection_df = initial_state(df_selected)
    if len(err_msg) > 0:
        # 初始化失败
        draw_graph(draw_fault_detection_df, req_data, replacements)
        return err_msg

    # 设备初始化成功，故障检测
    err_msg, replacements, draw_fault_detection_df = fault_detection(draw_fault_detection_df, brkStMn, brkStRed,
                                                                     tplt_type)
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

    # Enter initial state
    # Tra_numGear
    begin_time = df_selected['timestamps'].iloc[0]

    condition1_1 = df_selected['Tra_numGear'] == 0  # 0th gear
    condition1_2 = df_selected['timestamps'] >= begin_time
    initial_state_df_1 = df_selected[condition1_1 & condition1_2]
    if len(initial_state_df_1) == 0:
        err_msg.append('initial state Tra_numGear =0 failure ')
        end_time = begin_time + 5
        replacements = main_brake_plausibility_check_replacements(is_fail="√")
        return ret_fault_detection(end_time, begin_time, replacements, err_msg, df_selected)

    # Epm_nEng
    begin_time = initial_state_df_1['timestamps'].iloc[0]

    condition2_1 = df_selected['timestamps'] >= begin_time
    condition2_2 = df_selected['Epm_nEng'] >= 600
    condition2_3 = df_selected['Epm_nEng'] <= 800  # 转速 >= 600rpm & 转速 <= 800rpm
    initial_state_df_2 = initial_state_df_1[condition2_1 & condition2_2 & condition2_3]
    if len(initial_state_df_2) == 0:
        end_time = begin_time + 5
        err_msg.append('initial state Epm_nEng ∈ [600,800] failure')
        replacements = main_brake_plausibility_check_replacements(is_fail="√")
        return ret_fault_detection(end_time, begin_time, replacements, err_msg, initial_state_df_1)
    return err_msg, replacements, initial_state_df_2


def fault_detection(initial_state_df: DataFrame, brkStMn: bool, brkStRed: bool, tplt_type: str):
    err_msg = []

    # Fault detection
    # 4. Brk_stMn
    begin_time = initial_state_df['timestamps'].iloc[0]
    condition4_1 = initial_state_df['timestamps'] >= begin_time
    condition4_2 = initial_state_df['Brk_stMn'] == brkStMn
    fault_detection_df_4 = initial_state_df[condition4_1 & condition4_2]
    if len(fault_detection_df_4) == 0:
        err_msg.append(f'fault detection Brk_stMn={brkStMn} failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="❌", is_fail="√")
        return ret_fault_detection(begin_time + 5, begin_time - 2, replacements, err_msg, initial_state_df)

    # 5. Brk_stRed
    # begin_time = fault_detection_df_4['timestamps'].iloc[0]
    condition5_1 = fault_detection_df_4['timestamps'] >= begin_time
    condition5_2 = fault_detection_df_4['Brk_stRed'] == brkStRed
    fault_detection_df_5 = fault_detection_df_4[condition5_1 & condition5_2]
    if len(fault_detection_df_5) == 0:
        err_msg.append(f'fault detection Brk_stRed={brkStRed} failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="❌", is_fail="√")
        return ret_fault_detection(begin_time + 5, begin_time - 2, replacements, err_msg, fault_detection_df_4)

    # 6. DFC_BrkPlausChk, 故障标记了
    # begin_time = fault_detection_df_5['timestamps'].iloc[0]
    signals_dfes = find_columns_with_dfc_err_type(fault_detection_df_5, FAULT_TYPE_MAPPING.get(tplt_type))
    if len(signals_dfes) == 0:
        err_msg.append(f'fault detection DFC_BrkPlausChk is setted  failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="√", dfc_brkplauschk='❌', is_fail="√")
        return ret_fault_detection(begin_time + 5, begin_time - 2, replacements, err_msg, fault_detection_df_5)

    condition6 = fault_detection_df_5[signals_dfes[0]] == FAULT_TYPE_MAPPING.get('main_brake_plausibility_check')
    fault_detection_df_6 = fault_detection_df_5[condition6]
    # begin_time = fault_detection_df_6['timestamps'].iloc[0]

    # 6.1 Brk_st
    condition7 = fault_detection_df_6['Brk_st'] == 1
    fault_detection_df_7 = fault_detection_df_6[condition7]
    if len(fault_detection_df_7) == 0:
        err_msg.append(f'fault detection Brk_st=1 failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="√", dfc_brkplauschk='√', brk_st='❌',
                                                                  is_fail="√")
        return ret_fault_detection(begin_time + 5, begin_time - 2, replacements, err_msg, fault_detection_df_6)

    # DFC_BrkNpl*
    is_contains = err_type_contains_strings(fault_detection_df_6, 'DFC_BrkNpl')
    if not is_contains:
        err_msg.append(f'fault detection failure DFC_BrkNpl*  will exists ')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="√", dfc_brkplauschk='√', brk_st='√',
                                                                  is_dfc_brknpl='❌',
                                                                  is_fail="√")
        return ret_fault_detection(begin_time + 5, begin_time - 2, replacements, err_msg, fault_detection_df_6)

    # Everything is OK.
    replacements = main_brake_plausibility_check_replacements(brk_stmn="√", dfc_brkplauschk='√', brk_st='√',
                                                              is_dfc_brkplauschk='√', is_dfc_brknpl='√', is_pass='√')
    end_time = fault_detection_df_6['timestamps'].iloc[-1]
    return ret_fault_detection(end_time, begin_time,replacements, err_msg,  fault_detection_df_5)


def draw_graph(draw_fault_detection_df: DataFrame, req_data: ReqPOJO, replacements: map):
    # 特征列
    signals = ['Tra_numGear', 'Epm_nEng', 'Brk_stMn', 'Brk_stRed', 'Brk_st']

    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name

    output_path = replace_variables_in_doc(replacements, draw_fault_detection_df, signals, req_data)
    return output_path
