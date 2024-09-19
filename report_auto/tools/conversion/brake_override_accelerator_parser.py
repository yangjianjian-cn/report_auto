import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from constant.faultType import FAULT_TYPE_MAPPING
from constant.replacements import brake_override_accelerator_replacements
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.csv_column_rename import find_columns_with_dfc_err_type
from tools.report.report_generation import replace_variables_in_doc

'''csvPath: str, outputPath: str, docTemplate: str'''
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def brake_override_accelerator(req_data: ReqPOJO) -> list:
    # 读取csv测量文件
    df_selected = pd.read_csv(req_data.csv_path, encoding='utf8')

    # 设备初始化
    err_msg, draw_fault_detection_df = initial_state(df_selected)
    if len(err_msg) > 0:
        replacements = brake_override_accelerator_replacements(isfail='√')
        draw_img(draw_fault_detection_df, req_data, replacements)
        return err_msg

    # 设备初始化成功,故障检测
    err_msg, draw_fault_detection_df, replacements = fault_detection(draw_fault_detection_df)
    if len(err_msg) > 0:
        draw_img(draw_fault_detection_df, req_data, replacements)
        return err_msg

    # 故障成功触发，输出到文件
    output_path = draw_img(draw_fault_detection_df, req_data, replacements)
    err_msg.append(f'succeed:{output_path}')
    return err_msg


def r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements):
    end_time = end_time + 5 if end_time is not None else begin_time + 5
    draw_fault_detection_df = initial_state_df[
        (initial_state_df['timestamps'] >= begin_time) & (initial_state_df['timestamps'] <= end_time)]
    return err_msg, draw_fault_detection_df, replacements


def initial_state(df_selected: DataFrame):
    err_msg = []
    begin_time = end_time = None

    # 1.Enter initial state
    condition1 = df_selected['Tra_numGear'] >= 1  # 档位
    df_selected = df_selected[condition1]
    if len(df_selected) >= 0:
        begin_time = df_selected.iloc[0]['timestamps']
        logging.info(f"initial state Tra_numGear >=1 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state Tra_numGear >=1 failed')
        end_time = end_time + 5 if end_time is not None else begin_time + 5
        draw_fault_detection_df = df_selected[
            df_selected['timestamps'] >= begin_time & df_selected['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    condition2 = df_selected['VehV_v'] >= 10  # 车速 12
    df_selected = df_selected[condition2]
    if len(df_selected) > 0:
        end_time = df_selected.iloc[-1]['timestamps']
        logging.info(f"initial state VehV_v >=10 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state VehV_v >=10 failed')
        end_time = end_time + 5 if end_time is not None else begin_time + 5
        draw_fault_detection_df = df_selected[
            df_selected['timestamps'] >= begin_time & df_selected['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    condition3 = df_selected['APP_r'] >= 20  # 油门 >= 20%
    df_selected = df_selected[condition3]
    if len(df_selected) > 0:
        end_time = df_selected.iloc[-1]['timestamps']
        logging.info(f"initial state APP_r >=20 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state APP_r >=20 failed')
        end_time = end_time + 5 if end_time is not None else begin_time + 5
        draw_fault_detection_df = df_selected[
            df_selected['timestamps'] >= begin_time & df_selected['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    condition4 = df_selected['Epm_nEng'] >= 1200  # 转速 >= 1200rpm
    df_selected = df_selected[condition4]
    if len(df_selected) > 0:
        end_time = df_selected.iloc[-1]['timestamps']
        logging.info(f"initial state Epm_nEng >=1200 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state Epm_nEng >=1200 failed')
        end_time = end_time + 5 if end_time is not None else begin_time + 5
        draw_fault_detection_df = df_selected[
            df_selected['timestamps'] >= begin_time & df_selected['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    condition5 = df_selected['CEngDsT_t'] >= 25  # 水温大于等于25℃
    df_selected = df_selected[condition5]
    if len(df_selected) > 0:
        end_time = df_selected.iloc[-1]['timestamps']
        logging.info(f"initial state CEngDsT_t >=25 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state CEngDsT_t >=25 failed')
        end_time = end_time + 5 if end_time is not None else begin_time + 5
        draw_fault_detection_df = df_selected[
            df_selected['timestamps'] >= begin_time & df_selected['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    return err_msg, df_selected


def fault_detection(initial_state_df: DataFrame):
    err_msg = []
    begin_time = end_time = None

    # 2. Fault detection
    # Brk_stMn
    condition6 = initial_state_df['Brk_stMn'] == True
    fault_detection_df = initial_state_df[condition6]
    if len(fault_detection_df) > 0:
        begin_time = fault_detection_df['timestamps'].iloc[0] if not fault_detection_df.empty else 0
        logging.info(f"Fault detection:Brk_stMn=True succeed:{len(fault_detection_df)}")
    else:
        err_msg.append('Fault detection:Brk_stMn=True failed')
        replacements = brake_override_accelerator_replacements(isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # Brk_stRed
    condition7 = fault_detection_df['Brk_stRed'] == True
    fault_detection_df = fault_detection_df[condition7]
    if len(fault_detection_df) > 0:
        end_time = fault_detection_df['timestamps'].iloc[-1] if not fault_detection_df.empty else 0
        logging.info(f"Fault detection:Brk_stRed=True succeed:{len(fault_detection_df)}")
    else:
        err_msg.append('Fault detection:Brk_stRed=True failed')
        replacements = brake_override_accelerator_replacements(isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # Brk_st
    condition8 = fault_detection_df['Brk_st'] == 3
    fault_detection_df = fault_detection_df[condition8]
    if len(fault_detection_df) > 0:
        end_time = fault_detection_df['timestamps'].iloc[-1] if not fault_detection_df.empty else 0
        logging.info(f"Fault detection:Brk_st=3 succeed:{len(fault_detection_df)}")
    else:
        err_msg.append('Fault detection:Brk_st=3 failed')
        replacements = brake_override_accelerator_replacements(brk_st='❌', isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # APP_bPlaBrk
    condition9 = fault_detection_df['APP_bPlaBrk'] == 1
    fault_detection_df = fault_detection_df[condition9]
    if len(fault_detection_df) > 0:
        end_time = fault_detection_df['timestamps'].iloc[-1] if not fault_detection_df.empty else 0
        logging.info("Fault detection:APP_bPlaBrk=1 succeed")
    else:
        err_msg.append('Fault detection:APP_bPlaBrk=1 failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='❌', isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # APP_rUnFlt
    condition10 = fault_detection_df['APP_rUnFlt'] > 0
    fault_detection_df = fault_detection_df[condition10]
    if len(fault_detection_df) > 0:
        end_time = fault_detection_df['timestamps'].iloc[-1] if not fault_detection_df.empty else 0
        logging.info("Fault detection:APP_rUnFlt > 0 succeed")
    else:
        err_msg.append('Fault detection:APP_rUnFlt > 0 failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='❌', isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # APP_r
    condition11 = fault_detection_df['APP_r'] == 0
    fault_detection_df = fault_detection_df[condition11]
    if len(fault_detection_df) > 0:
        end_time = fault_detection_df['timestamps'].iloc[-1] if not fault_detection_df.empty else 0
        logging.info("Fault detection:APP_r == 0 succeed ")
    else:
        err_msg.append('Fault detection:APP_r == 0 failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='❌',
                                                               isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # DFC_APPPlausBrk
    signals_dfes = find_columns_with_dfc_err_type(fault_detection_df,
                                                  FAULT_TYPE_MAPPING.get('brake_override_accelerator'))
    if len(signals_dfes) > 0:
        logging.info("DFC_APPPlausBrk is set")
    else:
        err_msg.append('Fault detection:APP_r == 0 failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='√',
                                                               result='❌', isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # fault detection succeed
    total_time_spent = end_time + 5 - begin_time
    replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='√',
                                                           result='√', ispass='√', total_time_spent=total_time_spent)
    return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)


def draw_img(draw_fault_detection_df: DataFrame, req_data: ReqPOJO, replacements: map):
    signals = ['Brk_st', 'APP_bPlaBrk', 'APP_rUnFlt', 'APP_r']
    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name

    output_path = replace_variables_in_doc(replacements, draw_fault_detection_df, signals, req_data)
    return output_path

# req_data = ReqPOJO()
# req_data.csv_path = r'C:\Users\Administrator\Downloads\output\MST_Test\csv\APP_PL_BR_1.csv'
# brake_override_accelerator(req_data)
