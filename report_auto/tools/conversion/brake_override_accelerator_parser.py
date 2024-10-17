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
    begin_time = df_selected.iloc[0]['timestamps']

    condition1 = df_selected['Tra_numGear'] == 1  # 档位 1
    df_selected_1 = df_selected[condition1]
    if len(df_selected_1) == 0:
        err_msg.append('initial state Tra_numGear =1 failed')
        draw_fault_detection_df = df_selected[
            df_selected['timestamps'] >= begin_time & df_selected['timestamps'] <= begin_time + 5]
        return err_msg, draw_fault_detection_df

    begin_time = df_selected_1.iloc[0]['timestamps']
    condition2 = df_selected_1['VehV_v'] > 0  # 车速 0
    df_selected_2 = df_selected_1[condition2]
    if len(df_selected_2) == 0:
        err_msg.append('initial state VehV_v >=10 failed')
        draw_fault_detection_df = df_selected_1[
            df_selected_1['timestamps'] >= begin_time & df_selected_1['timestamps'] <= begin_time + 5]
        return err_msg, draw_fault_detection_df

    begin_time = df_selected_2.iloc[0]['timestamps']
    condition4 = df_selected_2['Epm_nEng'] >= 400  # 转速 >= 400rpm
    df_selected_4 = df_selected_2[condition4]
    if len(df_selected_4) == 0:
        err_msg.append('initial state Epm_nEng >=400 failed')
        draw_fault_detection_df = df_selected_2[
            df_selected_2['timestamps'] >= begin_time & df_selected_2['timestamps'] <= begin_time + 5]
        return err_msg, draw_fault_detection_df

    begin_time = df_selected_4.iloc[0]['timestamps']
    condition5 = df_selected_4['CEngDsT_t'] >= 25  # 水温大于等于25℃
    df_selected_5 = df_selected_4[condition5]
    if len(df_selected_5) == 0:
        draw_fault_detection_df = df_selected_4[
            df_selected_4['timestamps'] >= begin_time & df_selected_4['timestamps'] <= begin_time + 5]
        return err_msg, draw_fault_detection_df

    # df_selected_4数据集中，APP_r >= 20 存在即可
    begin_time = df_selected_5.iloc[0]['timestamps']
    condition3 = df_selected_5['APP_r'] >= 20  # 油门 >= 25%
    df_selected_3 = df_selected_5[condition3]
    if len(df_selected_3) == 0:
        err_msg.append('initial state APP_r >=20 failed')
        draw_fault_detection_df = df_selected_5[
            df_selected_5['timestamps'] >= begin_time & df_selected_5['timestamps'] <= begin_time + 5]
        return err_msg, draw_fault_detection_df

    return err_msg, df_selected_5


def fault_detection(initial_state_df: DataFrame):
    err_msg = []

    # 2. Fault detection
    begin_time = initial_state_df.iloc[0]['timestamps']
    # Brk_stMn
    condition6 = initial_state_df['Brk_stMn'] == True
    fault_detection_df_6 = initial_state_df[condition6]
    if len(fault_detection_df_6) == 0:
        err_msg.append('Fault detection:Brk_stMn=True failed')
        replacements = brake_override_accelerator_replacements(isfail='√')
        return r_fault_detection(begin_time + 5, begin_time, initial_state_df, err_msg, replacements)

    # Brk_stRed
    begin_time = fault_detection_df_6.iloc[0]['timestamps']
    condition7 = fault_detection_df_6['Brk_stRed'] == True
    fault_detection_df_7 = fault_detection_df_6[condition7]
    if len(fault_detection_df_7) == 0:
        err_msg.append('Fault detection:Brk_stRed=True failed')
        replacements = brake_override_accelerator_replacements(isfail='√')
        return r_fault_detection(begin_time + 5, begin_time, fault_detection_df_6, err_msg, replacements)

    # Brk_st
    begin_time = fault_detection_df_7.iloc[0]['timestamps']
    condition8 = fault_detection_df_7['Brk_st'] == 3
    fault_detection_df_8 = fault_detection_df_7[condition8]
    if len(fault_detection_df_8) == 0:
        err_msg.append('Fault detection:Brk_st=3 failed')
        replacements = brake_override_accelerator_replacements(brk_st='❌', isfail='√')
        return r_fault_detection(begin_time + 5, begin_time, fault_detection_df_7, err_msg, replacements)

    # 4.Press brake simultaneously (APP still pressed), until Brk_st=3 and hold it for some time (10sec)
    begin_time = fault_detection_df_8.iloc[0]['timestamps']

    # fault_detection_df_8数据集中，APP_bPlaBrk=1，存在即可
    condition9 = fault_detection_df_8['APP_bPlaBrk'] == 1
    fault_detection_df_9 = fault_detection_df_8[condition9]
    if len(fault_detection_df_9) == 0:
        err_msg.append('Fault detection:APP_bPlaBrk=1 failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='❌', isfail='√')
        return r_fault_detection(begin_time + 5, begin_time, fault_detection_df_8, err_msg, replacements)

    #  fault_detection_df_8数据集中，APP_rUnFlt >0 ,存在即可
    condition10 = fault_detection_df_8['APP_rUnFlt'] > 0
    fault_detection_df_10 = fault_detection_df_8[condition10]
    if len(fault_detection_df_10) == 0:
        err_msg.append('Fault detection:APP_rUnFlt > 0 failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='❌', isfail='√')
        return r_fault_detection(begin_time + 5, begin_time, fault_detection_df_8, err_msg, replacements)

    # fault_detection_df_8数据集，APP_r=0存在即可
    condition11 = fault_detection_df_8['APP_r'] == 0
    fault_detection_df_11 = fault_detection_df_8[condition11]
    if len(fault_detection_df_11) == 0:
        err_msg.append('Fault detection:APP_r == 0 failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='❌',
                                                               isfail='√')
        return r_fault_detection(begin_time + 5, begin_time, fault_detection_df_8, err_msg, replacements)

    # fault_detection_df_8数据集，DFC_APPPlausBrk异常出现即可
    signals_dfes = find_columns_with_dfc_err_type(fault_detection_df_8,FAULT_TYPE_MAPPING.get('brake_override_accelerator'))
    if len(signals_dfes) ==0:
        err_msg.append('Fault detection: DFC_APPPlausBrk is set failed')
        replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='√',
                                                               result='❌', isfail='√')
        return r_fault_detection(begin_time + 5, begin_time, fault_detection_df_8, err_msg, replacements)

    # fault detection succeed，计算end_time
    condition12 = fault_detection_df_8[signals_dfes[0]] == FAULT_TYPE_MAPPING.get('brake_override_accelerator')
    fault_detection_df_12 = fault_detection_df_8[condition12]
    end_time = fault_detection_df_12['timestamps'].iloc[-1]
    total_time_spent = end_time - begin_time
    replacements = brake_override_accelerator_replacements(brk_st='√', app_bplabrk='√', app_runflt='√', app_r='√',
                                                           result='√', ispass='√', total_time_spent=total_time_spent)
    return r_fault_detection(end_time, begin_time, fault_detection_df_8, err_msg, replacements)


def draw_img(draw_fault_detection_df: DataFrame, req_data: ReqPOJO, replacements: map):
    signals = ['Brk_st', 'APP_bPlaBrk', 'APP_rUnFlt', 'APP_r']
    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name

    # print(draw_fault_detection_df)
    output_path = replace_variables_in_doc(replacements, draw_fault_detection_df, signals, req_data)
    return output_path
