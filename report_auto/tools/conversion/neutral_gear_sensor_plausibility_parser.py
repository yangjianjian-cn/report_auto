__coding__ = "utf-8"

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from constant.replacements import neutral_gear_sensor_plausibility_replacements
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.report_common import ret_fault_detection
from tools.report.report_generation import replace_variables_in_doc

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def neutral_gear_sensor_plausibility(req_data: ReqPOJO):
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
    # 1.Enter initial state
    err_msg = []
    begin_time = None
    end_time = None
    replacements = {}

    condition1 = df_selected['CoEng_st'] == 'COENG_RUNNING'
    initial_state_df = df_selected[condition1]
    if len(initial_state_df) > 0:
        begin_time = initial_state_df.iloc[0]['timestamps']
        logging.info(f"initial state Tra_numGear =0 succeed:{len(initial_state_df)}")
    else:
        err_msg.append('initial state Tra_numGear =0 failure ')
        replacements = neutral_gear_sensor_plausibility_replacements(is_fail='√', gbx_stnpos='❌ ')
        return ret_fault_detection(end_time, begin_time, replacements, err_msg, initial_state_df)

    condition2 = initial_state_df['VehV_v'] > 0
    initial_state_df = initial_state_df[condition2]
    if len(initial_state_df) > 0:
        logging.info(f"initial state VehV_v > 0 succeed:{len(initial_state_df)}")
    else:
        err_msg.append('initial state VehV_v > 0 failure ')
        replacements = neutral_gear_sensor_plausibility_replacements(is_fail='√', gbx_stnpos='❌ ')
        return ret_fault_detection(end_time, begin_time, replacements, err_msg, initial_state_df)

    return err_msg, replacements, initial_state_df


def fault_detection(initial_state_df: DataFrame):
    begin_time = None
    end_time = None
    err_msg = []

    # 2.Fault detection
    condition3 = initial_state_df['Gbx_stNPos'] == 0
    fault_detection_df = initial_state_df[condition3]
    if len(fault_detection_df) > 0:
        begin_time = fault_detection_df.iloc[0]['timestamps']
        logging.info(f"fault detection Gbx_stNPos =0 succeed:{len(fault_detection_df)}")
    else:
        err_msg.append('fault detection Gbx_stNPos =0 failure ')
        replacements = neutral_gear_sensor_plausibility_replacements(is_fail='√', gbx_stnpos='❌ ')
        return ret_fault_detection(end_time, begin_time, replacements, err_msg, fault_detection_df)

    # 定义需要检查的档位列表
    gbx_stgearshftdet_is1 = None
    dfc_gbxnposnpl_set = None
    gears_to_check = [1, 2, 3, 4, 5]
    for gear in gears_to_check:
        # 找到第一次转换到该档位的索引
        first_transition_index = fault_detection_df.index[fault_detection_df['Tra_numGear'] == gear][0]
        if first_transition_index >= 1:
            # 获取索引为 first_transition_index 的行数据
            current_gbx_stgearshftdet_row = fault_detection_df.loc[first_transition_index]
            # 获取 'Gbx_stGearShftDet' 列的值
            current_gbx_stgearshftdet = current_gbx_stgearshftdet_row['Gbx_stGearShftDet']
            # 获取 'timestamps' 列的值
            end_time = current_gbx_stgearshftdet_row['timestamps']

            # 检查 'Gbx_stGearShftDet' 列的值是否为 1
            if current_gbx_stgearshftdet == 1:
                gbx_stgearshftdet_is1 = True
                # 动态生成所有 DFES_numDFC 列的名称
                dfc_columns = [f'DFES_numDFC_[{i}]' for i in range(10)]
                # 提取这些列的值，并存储在一个字典中
                dfc_values = {col: current_gbx_stgearshftdet_row[col] for col in dfc_columns}
                # 遍历所有 DFES_numDFC 列的值
                for dfc_col, dfc_val in dfc_values.items():
                    # 检查该值是否等于 'DFC_GbxNPosNpl'
                    if dfc_val == 'DFC_GbxNPosNpl':
                        # 执行相应的操作，例如记录或处理
                        dfc_gbxnposnpl_set = True  # 退出内层循环
            if dfc_gbxnposnpl_set:
                break  # 退出最外层循环

    # Gbx_stGearShftDet =1
    if gbx_stgearshftdet_is1:
        logging.info(f"fault detection Gbx_stGearShftDet =1 succeed")
    else:
        err_msg.append(f"fault detection Gbx_stGearShftDet =1 failure")
        replacements = neutral_gear_sensor_plausibility_replacements(is_fail='√', gbx_stgearshftdet='❌ ',
                                                                     gbx_stnpos='√')
        return ret_fault_detection(end_time, begin_time, replacements, err_msg, fault_detection_df)

    # DFC_GbxNPosNpl is SET
    if dfc_gbxnposnpl_set:
        logging.info(f"fault detection DFC_GbxNPosNpl is SET succeed")
    else:
        err_msg.append(f"fault detection DFC_GbxNPosNpl is SET failure")
        replacements = neutral_gear_sensor_plausibility_replacements(is_fail='√', dfc_gbxnposnpl='❌ ',
                                                                     gbx_stgearshftdet='√', gbx_stnpos='√')
        return ret_fault_detection(end_time, begin_time, replacements, err_msg, fault_detection_df)

    replacements = neutral_gear_sensor_plausibility_replacements(is_pass='√', dfc_gbxnposnpl='√', gbx_stgearshftdet='√',
                                                                 gbx_stnpos='√')
    return ret_fault_detection(end_time, begin_time, replacements, err_msg, fault_detection_df)


def draw_graph(draw_fault_detection_df: DataFrame, req_data: ReqPOJO, replacements: map):
    logging.info(f"模板参数:{replacements}")

    signals = ['CoEng_st', 'VehV_v', 'Gbx_stNPos', 'Tra_numGear', 'Gbx_stGearShftDet', 'DFC_st.DFC_GbxNPosNpl']
    logging.info(f"信号列:{signals}")

    output_name = Path(req_data.csv_path).stem
    req_data.doc_output_name = output_name
    logging.info(f"文件名:{output_name}")

    output_path = replace_variables_in_doc(replacements, draw_fault_detection_df, signals, req_data)
    return output_path
