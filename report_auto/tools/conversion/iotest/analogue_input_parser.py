__coding__ = "utf-8"

import logging
import os

import pandas as pd

from constant.TestCaseType import TestCaseType
from pojo.MSTReqPOJO import ReqPOJO
from tools.report.xlsm_report_generation import analogue_input_report
from tools.utils.MathUtils import truncate_to_one_decimal_place, getBit4, getBit2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

"""
csvPath: /outputpath/测试团队/测试场景/测试功能
outputPath：/outputpath/测试团队/测试区域
"""


def analogue_input(req_data: ReqPOJO) -> str:
    logging.info(f"csv_path:{req_data.csv_path}")
    logging.info(f"output_path:{req_data.output_path}")
    level1, level2, level3, level4 = 'n/a', 'n/a', 'n/a', 'n/a'

    # 使用 os.walk() 遍历目录及其子目录
    all_files = []
    for root, dirs, files in os.walk(req_data.csv_path):
        for file in files:
            all_files.append(os.path.join(root, file))

    # 打印结果以验证
    for dat_file in all_files:
        if 'Level1' in dat_file:
            df_selected = pd.read_csv(dat_file, encoding='utf8')

            # ########## 校验level1是否通过
            # 填充 NaN 值为 0
            df_selected['APP_uRaw1unLim'] = df_selected['APP_uRaw1unLim'].fillna(0)
            # 选择 'APP_uRaw1unLim'列，并对每个元素执行除以 1000 取整的操作
            result_set = set(df_selected['APP_uRaw1unLim'].apply(truncate_to_one_decimal_place))
            # 过滤掉 0 和 5
            filtered_set = {value for value in result_set if value not in [0, 5]}
            element_count = len(filtered_set)
            if element_count > 0:
                # level1符合条件
                level1 = 'passed'

        if 'Level2-4' in dat_file:
            df_selected = pd.read_csv(dat_file, encoding='utf8')

            def check_row(row):
                if row['APP_uRaw1unLim'] > row['APP_uRaw1SRCHigh_C']:  # 电压 > 上限电压
                    return 'passed' if getBit4(row['DFC_st.DFC_SRCHighAPP1']) == '1' else 'failed'
                elif row['APP_uRaw1unLim'] < row['APP_uRaw1SRCLow_C']:  # 电压 < 下限电压
                    return 'passed' if getBit4(row['DFC_st.DFC_SRCLowAPP1']) == '1' else 'failed'

            df_selected['Level2'] = df_selected.apply(check_row, axis=1)
            passed_count = (df_selected['Level2'] == 'passed').sum()
            if passed_count > 0:
                level2 = 'passed'
            else:
                level2 = 'failed'

            # 电压超过上限-触发故障
            bit4_last_row_timestamps = 0
            filtered_df = df_selected[(df_selected['APP_uRaw1unLim'] > df_selected['APP_uRaw1SRCHigh_C'])]
            if len(filtered_df) != 0:
                # bit2= 1 激活，故障触发
                filtered_df_bit2 = filtered_df[(filtered_df['DFC_st.DFC_SRCHighAPP1'].apply(getBit2) == '1')]
                if len(filtered_df_bit2) != 0:
                    # 最后激活时间
                    bit2_last_row_timestamps = filtered_df_bit2.iloc[-1]['timestamps']
                    logging.info(f"故障激活时间:{bit2_last_row_timestamps}")
                    # 故障发生了
                    filtered_df_bit4 = filtered_df[(filtered_df['timestamps'] > bit2_last_row_timestamps) & (
                            filtered_df['DFC_st.DFC_SRCHighAPP1'].apply(getBit4) == '1')]
                    if filtered_df_bit4.empty:
                        level3 = 'failed'
                    else:
                        # 最后故障时间
                        level3 = 'passed'
                        bit4_last_row_timestamps = filtered_df_bit4.iloc[-1]['timestamps']
                        logging.info(f"故障结束时间:{bit4_last_row_timestamps}")

            # 电压超过上限-故障恢复
            filtered_df = df_selected[(df_selected['timestamps'] > bit4_last_row_timestamps)]
            if len(filtered_df) != 0:
                # 故障恢复激活中
                filtered_df_bit2 = filtered_df[(filtered_df['DFC_st.DFC_SRCHighAPP1'].apply(getBit2) == '1')]
                if len(filtered_df_bit2) != 0:
                    # 故障恢复-激活-结束时间
                    bit2_last_row_timestamps = filtered_df_bit2.iloc[-1]['timestamps']
                    logging.info(f"故障恢复时间:{bit2_last_row_timestamps}")

                    filtered_df_bit4 = filtered_df[filtered_df['timestamps'] > bit2_last_row_timestamps]
                    if len(filtered_df_bit4) != 0:
                        filtered_df_bit4 = filtered_df_bit4.head(1)
                        if getBit4(filtered_df_bit4['DFC_st.DFC_SRCHighAPP1']) == '0':
                            level3 = 'passed'
                        else:
                            level3 = 'failed'

            # raw值超限时，检查目标值是否被default值替代
            filtered_df = df_selected[df_selected['APP_uRaw1unLim'] > df_selected['APP_uRaw1SRCHigh_C']]
            filtered_df = filtered_df[filtered_df['DFC_st.DFC_SRCHighAPP1'].apply(getBit4) == '1']
            if len(filtered_df) != 0:
                # 检查 'APP_uRaw1' 和 'APP_uRaw1Def_C' 是否完全相等
                are_equal = (filtered_df['APP_uRaw1'] == filtered_df['APP_uRaw1Def_C']).all()
            if are_equal:
                level4 = "passed"
            else:
                level4 = "failed"

    # ########## 校验level2是否通过
    req_data.template_name = TestCaseType.IOTest_Man_Tmplt.name
    xlsm_path = analogue_input_report(req_data, level1, level2, level3, level4)
    return xlsm_path
