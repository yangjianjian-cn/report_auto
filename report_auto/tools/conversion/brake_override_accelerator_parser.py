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

    # 1.Enter initial state
    condition1 = df_selected['Tra_numGear'] == 1  # 档位 1
    df_selected_1 = df_selected[condition1]
    if len(df_selected_1) >= 0:
        logging.info(f"initial state Tra_numGear >=1 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state Tra_numGear >=1 failed')
        begin_time = df_selected.iloc[0]['timestamps']
        end_time = begin_time + 5
        draw_fault_detection_df = df_selected[df_selected['timestamps'] >= begin_time & df_selected['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    condition2 = df_selected_1['VehV_v'] > 0  # 车速 0
    df_selected_2 = df_selected_1[condition2]
    if len(df_selected_2) > 0:
        logging.info(f"initial state VehV_v >=10 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state VehV_v >=10 failed')
        begin_time = df_selected_1.iloc[0]['timestamps']
        end_time = begin_time + 5
        begin_time = begin_time - 5
        draw_fault_detection_df = df_selected_1[df_selected_1['timestamps'] >= begin_time & df_selected_1['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    condition4 = df_selected_2['Epm_nEng'] >= 400  # 转速 >= 400rpm
    df_selected_4 = df_selected_2[condition4]
    if len(df_selected_4) > 0:
        logging.info(f"initial state Epm_nEng >=1200 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state Epm_nEng >=1200 failed')
        begin_time = df_selected_2.iloc[0]['timestamps']
        end_time = begin_time + 5
        draw_fault_detection_df = df_selected_2[df_selected_2['timestamps'] >= begin_time & df_selected_2['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    condition5 = df_selected_4['CEngDsT_t'] >= 25  # 水温大于等于25℃
    df_selected_5 = df_selected_4[condition5]
    if len(df_selected_5) > 0:
        logging.info(f"initial state CEngDsT_t >=25 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state CEngDsT_t >=25 failed')
        begin_time = df_selected_4.iloc[0]['timestamps']
        end_time = begin_time + 5
        draw_fault_detection_df = df_selected_4[df_selected_4['timestamps'] >= begin_time & df_selected_4['timestamps'] <= end_time]
        return err_msg, draw_fault_detection_df

    condition3 = df_selected_5['APP_r'] >= 25  # 油门 >= 25%
    df_selected_3 = df_selected_5[condition3]
    if len(df_selected_3) > 0:
        logging.info(f"initial state APP_r >=20 succeed: {len(df_selected)}")
    else:
        err_msg.append('initial state APP_r >=20 failed')
        begin_time = df_selected_5.iloc[0]['timestamps']
        end_time = begin_time + 5
        draw_fault_detection_df = df_selected_5[df_selected_4['timestamps'] >= begin_time & df_selected_5['timestamps'] <= end_time ]
        return err_msg, draw_fault_detection_df

    begin_time = df_selected_3.iloc[0]['timestamps']
    draw_fault_detection_df = df_selected[df_selected['timestamps'] >= begin_time]

    return err_msg, draw_fault_detection_df


def fault_detection(initial_state_df: DataFrame):
    err_msg = []
    g_begin_time = None
    g_begin_time = None

    # 2. Fault detection
    # Brk_stMn
    condition6 = initial_state_df['Brk_stMn'] == True
    fault_detection_df_6 = initial_state_df[condition6]
    if len(fault_detection_df_6) > 0:
        # 图表折线图开始时间
        g_begin_time = fault_detection_df_6['timestamps'].iloc[0] if not fault_detection_df_6.empty else 0
        logging.info(f"Fault detection:Brk_stMn=True succeed:{len(fault_detection_df_6)}")
    else:
        err_msg.append('Fault detection:Brk_stMn=True failed')

        begin_time = initial_state_df['timestamps'].iloc[0] if not initial_state_df.empty else 0
        end_time = begin_time + 5
        begin_time = begin_time - 5
        replacements = brake_override_accelerator_replacements(isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # Brk_stRed
    condition7 = fault_detection_df_6['Brk_stRed'] == True
    fault_detection_df_7 = fault_detection_df_6[condition7]
    if len(fault_detection_df_7) > 0:
        logging.info(f"Fault detection:Brk_stRed=True succeed:{len(fault_detection_df_7)}")
    else:
        err_msg.append('Fault detection:Brk_stRed=True failed')

        begin_time = fault_detection_df_6['timestamps'].iloc[0] if not fault_detection_df_6.empty else 0
        end_time = begin_time + 5
        begin_time = begin_time - 5

        replacements = brake_override_accelerator_replacements(isfail='√')
        return r_fault_detection(end_time, begin_time, fault_detection_df_6, err_msg, replacements)

    # Brk_st
    condition8 = fault_detection_df_7['Brk_st'] == 3
    fault_detection_df_8 = fault_detection_df_7[condition8]
    if len(fault_detection_df_8) > 0:
        logging.info(f"Fault detection:Brk_st=3 succeed:{len(fault_detection_df_8)}")
    else:
        err_msg.append('Fault detection:Brk_st=3 failed')
        begin_time = fault_detection_df_7['timestamps'].iloc[0] if not fault_detection_df_7.empty else 0
        end_time = begin_time + 5
        begin_time = begin_time - 5

        replacements = brake_override_accelerator_replacements(brk_st='❌', isfail='√')
        return r_fault_detection(end_time, begin_time, fault_detection_df_7, err_msg, replacements)

    # 4.Press brake simultaneously (APP still pressed), until Brk_st=3 and hold it for some time (10sec)
    # APP_bPlaBrk
    condition9 = fault_detection_df_8['APP_bPlaBrk'] == 1
    fault_detection_df_9 = fault_detection_df_8[condition9]
    if len(fault_detection_df_9) > 0:
        logging.info("Fault detection:APP_bPlaBrk=1 succeed")
    else:
        err_msg.append('Fault detection:APP_bPlaBrk=1 failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='❌', isfail='√')

        begin_time = fault_detection_df_8['timestamps'].iloc[0] if not fault_detection_df_8.empty else 0
        end_time = begin_time + 5
        begin_time = begin_time - 5

        return r_fault_detection(end_time, begin_time, fault_detection_df_8, err_msg, replacements)

    # APP_rUnFlt
    condition10 = fault_detection_df_8['APP_rUnFlt'] > 0
    fault_detection_df_10 = fault_detection_df_8[condition10]
    if len(fault_detection_df_10) > 0:
        logging.info("Fault detection:APP_rUnFlt > 0 succeed")
    else:
        err_msg.append('Fault detection:APP_rUnFlt > 0 failed')

        begin_time = fault_detection_df_8['timestamps'].iloc[0] if not fault_detection_df_8.empty else 0
        end_time = begin_time + 5
        begin_time = begin_time - 5

        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='❌', isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # APP_r
    condition11 = fault_detection_df_8['APP_r'] == 0
    fault_detection_df_11 = fault_detection_df_8[condition11]
    if len(fault_detection_df_11) > 0:
        logging.info("Fault detection:APP_r == 0 succeed ")
    else:
        err_msg.append('Fault detection:APP_r == 0 failed')
        begin_time = fault_detection_df_8['timestamps'].iloc[0] if not fault_detection_df_8.empty else 0
        end_time = begin_time + 5
        begin_time = begin_time - 5
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='❌',
                                                               isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # DFC_APPPlausBrk
    signals_dfes = find_columns_with_dfc_err_type(fault_detection_df_8, FAULT_TYPE_MAPPING.get('brake_override_accelerator'))
    if len(signals_dfes) > 0:
        logging.info("DFC_APPPlausBrk is set")
    else:
        err_msg.append('Fault detection: DFC_APPPlausBrk is set failed')

        begin_time = fault_detection_df_8['timestamps'].iloc[0] if not fault_detection_df_8.empty else 0
        end_time = begin_time + 5
        begin_time = begin_time - 5

        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='√',
                                                               result='❌', isfail='√')
        return r_fault_detection(end_time, begin_time, initial_state_df, err_msg, replacements)

    # fault detection succeed
    condition11 = fault_detection_df_8[signals_dfes[0]] == FAULT_TYPE_MAPPING.get('brake_override_accelerator')
    fault_detection_df_11 = fault_detection_df_8[condition11]
    g_end_time = fault_detection_df_11['timestamps'].iloc[-1] if not fault_detection_df_11.empty else 0
    total_time_spent = g_end_time - g_begin_time

    replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='√',
                                                           result='√', ispass='√', total_time_spent=total_time_spent)
    return r_fault_detection(g_end_time, g_begin_time, initial_state_df, err_msg, replacements)


def draw_img(draw_fault_detection_df: DataFrame, req_data: ReqPOJO, replacements: map):
    signals = ['Brk_st', 'APP_bPlaBrk', 'APP_rUnFlt', 'APP_r']
    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name

    output_path = replace_variables_in_doc(replacements, draw_fault_detection_df, signals, req_data)
    return output_path

# req_data = ReqPOJO()
# req_data.csv_path = r'C:\Users\Administrator\Downloads\output\MST_Test\csv\APP_PL_BR_1.csv'
# brake_override_accelerator(req_data)
