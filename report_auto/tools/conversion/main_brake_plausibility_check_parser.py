import logging
from pathlib import Path

import pandas as pd

from pojo.MSTReqPOJO import ReqPOJO
from tools.report.report_generation import replace_variables_in_doc
from constant.replacements import main_brake_plausibility_check_replacements

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main_brake_plausibility_check(req_data: ReqPOJO) -> str:
    df_selected = pd.read_csv(req_data.csv_path, encoding='utf8')

    # Enter initial state
    condition1 = df_selected['Tra_numGear'] == 0  # 0th gear
    condition2 = df_selected['Epm_nEng'] >= 600
    condition3 = df_selected['Epm_nEng'] <= 800  # 转速 >= 600rpm and 转速 <= 800rpm
    fault_detection_df = df_selected[condition1 & condition2 & condition3]

    # Fault detection
    condition4 = fault_detection_df['Brk_stMn'] == True
    condition5 = fault_detection_df['Brk_stRed'] == False
    condition6 = fault_detection_df['DFC_st.DFC_BrkPlausChk'] == 251
    condition7 = fault_detection_df['Brk_st'] == 1
    fault_detection_df = fault_detection_df[condition4 & condition5 & condition6 & condition7]
    last_row = fault_detection_df.iloc[-1]  # #故障发生的结束行

    # #起始行
    fault_detection_df_idxs = fault_detection_df.index
    fault_detection_df_idx = fault_detection_df_idxs[0]
    # 确保索引不超出范围
    while fault_detection_df_idx > 0:
        # 减少索引值
        fault_detection_df_idx -= 1
        # 获取当前索引对应的行
        row = df_selected.iloc[fault_detection_df_idx]

        # 检查条件是否满足
        if row['Brk_stMn'] == True and row['Brk_stRed'] == False and row['Brk_st'] == 1 \
                and row['DFC_st.DFC_BrkPlausChk'] != 251:
            pass
        else:
            break
    fault_detection_df_idx += 1
    begin_row = df_selected.iloc[fault_detection_df_idx]  # # 故障发生的起始行

    # Error time:
    last_time = last_row['timestamps']
    begin_time = begin_row['timestamps']
    total_time_spent = last_time - begin_time
    logging.debug(f"last_time={last_time},begin_time={begin_time},error_time={total_time_spent}")

    # 绘制二维坐标轴，前后延5秒
    begin_time = begin_time + 5
    last_time = last_time + 5
    condition8 = df_selected['timestamps'] >= begin_time
    condition9 = df_selected['timestamps'] <= last_time
    fault_detection_df = df_selected[condition8 & condition9]

    # 占位符
    replacements = main_brake_plausibility_check_replacements(total_time_spent)

    signals = ['Epm_nEng', 'DDRC_DurDeb.Brk_tiPlausChkDebDef_C', 'Brk_st']
    # 时间戳转换为秒
    # fault_detection_df['DDRC_DurDeb.Brk_tiPlausChkDebDef_C'] = fault_detection_df['DDRC_DurDeb.Brk_tiPlausChkDebDef_C'].div(1000).round().astype
    fault_detection_df.loc[:, 'DDRC_DurDeb.Brk_tiPlausChkDebDef_C'] = (
        fault_detection_df['DDRC_DurDeb.Brk_tiPlausChkDebDef_C'].div(1000).round().astype(int))

    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name

    output_path = replace_variables_in_doc(replacements, fault_detection_df,signals,req_data)
    return output_path
