__coding__ = "utf-8"

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from constant.replacements import main_brake_plausibility_check_replacements
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.csv_column_rename import err_type_contains_strings
from tools.report.report_generation import replace_variables_in_doc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def brake_plausibility_check(req_data: ReqPOJO, brkStMn: bool, brkStRed: bool, tplt_type: str):
    df_selected = pd.read_csv(req_data.csv_path, encoding='utf8')

    # 设备初始化
    err_msg, replacements, draw_fault_detection_df = initial_state(df_selected)
    if len(err_msg) > 0:
        # 初始化失败
        draw_graph(draw_fault_detection_df, tplt_type, req_data, replacements)
        return err_msg

    # 设备初始化成功，故障检测
    err_msg, replacements, draw_fault_detection_df = fault_detection(draw_fault_detection_df, brkStMn, brkStRed)
    if len(err_msg) > 0:
        # 检测出现异常
        draw_graph(draw_fault_detection_df, tplt_type, req_data, replacements)
        return err_msg

    # 检测通过
    output_path = draw_graph(draw_fault_detection_df, tplt_type, req_data, replacements)
    err_msg.append(f"succeed:{output_path}")
    return err_msg


def ret_fault_detection(begin_time, end_time, err_msg: list, replacements: map, df: DataFrame):
    end_time = end_time + 5 if end_time is not None else begin_time + 5
    condition8 = df['timestamps'] >= begin_time
    condition9 = df['timestamps'] <= end_time
    draw_fault_detection_df = df[condition8 & condition9]
    return err_msg, replacements, draw_fault_detection_df


def initial_state(df_selected: DataFrame):
    err_msg = []
    begin_time = None
    end_time = None
    replacements ={}

    # Enter initial state
    # Tra_numGear
    condition1 = df_selected['Tra_numGear'] == 0  # 0th gear
    initial_state_df = df_selected[condition1]
    if len(initial_state_df) > 0:
        begin_time = initial_state_df.iloc[0]['timestamps']
        logging.info(f"initial state Tra_numGear =0 succeed:{len(initial_state_df)}")
    else:
        err_msg.append('initial state Tra_numGear =0 failure ')
        replacements = main_brake_plausibility_check_replacements(is_fail="√")
        return ret_fault_detection(begin_time, end_time, err_msg, replacements, initial_state_df)

    # Epm_nEng
    condition2 = df_selected['Epm_nEng'] >= 600
    condition3 = df_selected['Epm_nEng'] <= 800  # 转速 >= 600rpm and 转速 <= 800rpm
    initial_state_df = initial_state_df[condition1 & condition2 & condition3]
    if len(initial_state_df) > 0:
        end_time = initial_state_df.iloc[-1]['timestamps']
        logging.info(f"initial state Epm_nEng ∈ [600,800] succeed:{len(initial_state_df)}")
    else:
        err_msg.append('initial state Epm_nEng ∈ [600,800] failure')
        replacements = main_brake_plausibility_check_replacements(is_fail="√")
        return ret_fault_detection(begin_time, end_time, err_msg, replacements, initial_state_df)
    return err_msg,replacements,initial_state_df


def fault_detection(initial_state_df: DataFrame, brkStMn: bool, brkStRed: bool):
    begin_time = None
    end_time = None

    err_msg = []
    # Fault detection
    # Brk_stMn
    condition4 = initial_state_df['Brk_stMn'] == brkStMn
    fault_detection_df = initial_state_df[condition4]
    if len(fault_detection_df) > 0:
        begin_time = fault_detection_df.iloc[0]['timestamps']
        logging.info(f'fault detection Brk_stMn={brkStMn} succeed:{len(fault_detection_df)}')
    else:
        err_msg.append(f'fault detection Brk_stMn={brkStMn} failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="❌", is_fail="√")
        return ret_fault_detection(begin_time, end_time, err_msg, replacements, initial_state_df)

    # Brk_stRed
    condition5 = fault_detection_df['Brk_stRed'] == brkStRed
    fault_detection_df = fault_detection_df[condition5]
    if len(fault_detection_df) > 0:
        end_time = fault_detection_df.iloc[-1]['timestamps']
        logging.info(f'fault detection Brk_stRed={brkStRed} succeed:{len(fault_detection_df)}')
    else:
        err_msg.append(f'fault detection Brk_stRed={brkStRed} failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="❌", is_fail="√")
        return ret_fault_detection(begin_time, end_time, err_msg, replacements, initial_state_df)

    # 创建一个条件，用来筛选出那些第五个二进制位为1的行
    # 注意这里的第五位是从右边开始计数，下标为4
    # DFC_st.DFC_BrkPlausChk
    condition6 = (fault_detection_df['DFC_st.DFC_BrkPlausChk'] & 16) != 0  # 因为2^4=16
    fault_detection_df = fault_detection_df[condition6]
    if len(fault_detection_df) > 0:
        end_time = fault_detection_df.iloc[-1]['timestamps']
        logging.info(f'fault detection DFC_BrkPlausChk is setted succeed:{len(fault_detection_df)}')
    else:
        err_msg.append(f'fault detection DFC_BrkPlausChk is setted  failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="√", dfc_brkplauschk='❌', is_fail="√")
        return ret_fault_detection(begin_time, end_time, err_msg, replacements, initial_state_df)

    # Brk_st
    condition7 = fault_detection_df['Brk_st'] == 1
    fault_detection_df = fault_detection_df[condition7]
    if len(fault_detection_df) > 0:
        end_time = fault_detection_df.iloc[-1]['timestamps']
        logging.info(f'fault detection Brk_st=1 succeed:{len(fault_detection_df)}')
    else:
        err_msg.append(f'fault detection Brk_st=1 failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="√", dfc_brkplauschk='√', brk_st='❌',
                                                                  is_fail="√")
        return ret_fault_detection(begin_time, end_time, err_msg, replacements, initial_state_df)

    # DFC_BrkNpl*
    is_contains = err_type_contains_strings(fault_detection_df, 'DFC_BrkNpl')
    if is_contains:
        logging.info(f'fault detection DFC_BrkNpl*  will not be set succeed:{len(fault_detection_df)}')
    else:
        err_msg.append(f'fault detection DFC_BrkNpl*  will not be set failure')
        replacements = main_brake_plausibility_check_replacements(brk_stmn="√", dfc_brkplauschk='√', brk_st='√',
                                                                  is_dfc_brknpl='❌',
                                                                  is_fail="√")
        return ret_fault_detection(begin_time, end_time, err_msg, replacements, initial_state_df)

    # Everything is OK.
    replacements = main_brake_plausibility_check_replacements(brk_stmn="√", dfc_brkplauschk='√', brk_st='√',
                                                              is_dfc_brknpl='√',
                                                              is_pass='√')

    return ret_fault_detection(begin_time, end_time, err_msg, replacements, initial_state_df)


def draw_graph(draw_fault_detection_df: DataFrame, tplt_type: str, req_data: ReqPOJO, replacements: map):
    # 特征列
    signals = ['Tra_numGear', 'Epm_nEng', 'Brk_stMn', 'Brk_stRed', 'Brk_st']

    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name

    output_path = replace_variables_in_doc(replacements, draw_fault_detection_df, signals, req_data)
    return output_path
