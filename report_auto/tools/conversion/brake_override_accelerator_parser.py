from pathlib import Path

import pandas as pd

from constant.replacements import brake_override_accelerator_replacements
from pojo.MSTReqPOJO import ReqPOJO
from tools.report.report_generation import replace_variables_in_doc

'''csvPath: str, outputPath: str, docTemplate: str'''


def brake_override_accelerator(req_data: ReqPOJO) -> str:
    df_selected = pd.read_csv(req_data.csv_path, encoding='utf8')

    # 2.Enter initial state
    condition1 = df_selected['Tra_numGear'] >= 1  # 档位
    condition2 = df_selected['VehV_v'] >= 10  # 车速 12
    condition3 = df_selected['APP_r'] >= 20  # 油门 >= 20%
    condition4 = df_selected['Epm_nEng'] >= 1200  # 转速 >= 1200rpm
    condition5 = df_selected['CEngDsT_t'] >= 25  # 水温大于等于25℃
    fault_detection_df = df_selected[condition1 & condition2 & condition3 & condition4 & condition5]
    end_timestamp = fault_detection_df['timestamps'].iloc[-1]
    data_after_last_timestamp = df_selected[df_selected['timestamps'] > end_timestamp]

    # 3. Fault detection
    condition16 = data_after_last_timestamp['Brk_stMn'] == True
    condition17 = data_after_last_timestamp['Brk_stRed'] == True
    condition18 = data_after_last_timestamp['Brk_st'] == 3
    condition19 = data_after_last_timestamp['APP_bPlaBrk'] == 1
    condition20 = data_after_last_timestamp['APP_rUnFlt'] > 0
    condition21 = data_after_last_timestamp['APP_r'] == 0
    fault_detection_df = data_after_last_timestamp[
        condition16 & condition17 & condition18 & condition19 & condition20 & condition21]
    end_timestamp = fault_detection_df['timestamps'].iloc[-1] if not fault_detection_df.empty else 0

    # 4. Error time
    begin_timestamp = fault_detection_df['timestamps'].iloc[0] if not fault_detection_df.empty else 0
    total_time_spent = end_timestamp - begin_timestamp
    if total_time_spent is not None:
        total_time_spent *= 1000
    else:
        total_time_spent = 0

    # 5. word文档占位符
    replacements = brake_override_accelerator_replacements(total_time_spent)

    # 6.生成测试报告(前后延5s)
    begin_timestamp = begin_timestamp - 5
    end_timestamp = end_timestamp + 5
    fault_detection_df = df_selected[
        (df_selected['timestamps'] >= begin_timestamp) & (df_selected['timestamps'] <= end_timestamp)]

    signals = ['Brk_st', 'APP_bPlaBrk', 'APP_rUnFlt', 'APP_r']
    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name

    output_path = replace_variables_in_doc(replacements, fault_detection_df, signals, req_data)
    return output_path
