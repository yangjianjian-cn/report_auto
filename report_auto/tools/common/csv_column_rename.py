from typing import List

import pandas as pd
from pandas import DataFrame

from constant.TestCaseType import TestCaseType

'''csv文件列名重命名'''


def reMstDF(df: DataFrame, output_file_name: str) -> DataFrame:
    # 通用特征列
    dfes_list = ['DFES_numDFC_[0]', 'DFES_numDFC_[1]', 'DFES_numDFC_[2]', 'DFES_numDFC_[3]',
                 'DFES_numDFC_[4]', 'DFES_numDFC_[5]', 'DFES_numDFC_[6]', 'DFES_numDFC_[7]', 'DFES_numDFC_[8]',
                 'DFES_numDFC_[9]']
    need_include_column_list = []
    # 根据dat文件名称，提取特征列
    if TestCaseType.brake_override_accelerator.value in output_file_name.lower():
        # app_pl_br_1
        need_include_column_list = ['Tra_numGear', 'VehV_v', 'APP_r', 'Epm_nEng', 'CEngDsT_t', 'Brk_stMn', 'Brk_stRed',
                                    'APP_bPlaBrk', 'APP_rUnFlt', 'Brk_st', 'DFC_st.DFC_APPPlausBrk']

    elif TestCaseType.main_brake_plausibility_check.value in output_file_name.lower():
        # brk_04
        need_include_column_list = ['Tra_numGear', 'Epm_nEng', 'Brk_stMn', 'Brk_stRed', 'DFC_st.DFC_BrkPlausChk',
                                    'DDRC_DurDeb.Brk_tiPlausChkDebDef_C', 'Brk_st']

    elif TestCaseType.redundant_brake_plausibility_check.value in output_file_name.lower():
        # brk_05
        need_include_column_list = ['Tra_numGear', 'Epm_nEng', 'Brk_stMn', 'Brk_stRed', 'DFC_st.DFC_BrkPlausChk',
                                    'DDRC_DurDeb.Brk_tiPlausChkDebDef_C', 'Brk_st']

    elif TestCaseType.neutral_gear_sensor_plausibility_check.value in output_file_name.lower():
        # ngs_06
        need_include_column_list = ['CoEng_st', 'VehV_v', 'Gbx_stNPos', 'Tra_numGear', 'Gbx_stGearShftDet',
                                    'DFC_st.DFC_GbxNPosNpl']

    elif TestCaseType.plausibility_check_of_clth_stuck_top.value in output_file_name.lower():
        # clth_05
        need_include_column_list = ['CoEng_st', 'VehV_v', 'Clth_st', 'Tra_numGear', 'Clth_numLastVldGear',
                                    'DFC_st.DFC_ClthNplOpn']

    elif TestCaseType.plausibility_check_of_clth_stuck_bottom.value in output_file_name.lower():
        # clth_06
        need_include_column_list = ['CoEng_st', 'VehV_v', 'Clth_st', 'Clth_bAutoStrtEnaCond', 'Tra_numGear',
                                    'Clth_numLastVldGear', 'Clth_bClthPlausErr', 'DFC_st.DFC_ClthPlausChk']

    columns_to_include = need_include_column_list + dfes_list
    df = df[columns_to_include]

    # 二进制字符串 b'',转换为字符串
    if 'Brk_stMn' in df.columns:
        df.loc[:, 'Brk_stMn'] = df['Brk_stMn'].apply(lambda x: x.decode('utf-8'))
    if 'Brk_stRed' in df.columns:
        df.loc[:, 'Brk_stRed'] = df['Brk_stRed'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[0]'] = df['DFES_numDFC_[0]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[1]'] = df['DFES_numDFC_[1]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[2]'] = df['DFES_numDFC_[2]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[3]'] = df['DFES_numDFC_[3]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[4]'] = df['DFES_numDFC_[4]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[5]'] = df['DFES_numDFC_[5]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[6]'] = df['DFES_numDFC_[6]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[7]'] = df['DFES_numDFC_[7]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[8]'] = df['DFES_numDFC_[8]'].apply(lambda x: x.decode('utf-8'))
    df.loc[:, 'DFES_numDFC_[9]'] = df['DFES_numDFC_[9]'].apply(lambda x: x.decode('utf-8'))
    if 'CoEng_st' in df.columns:
        df.loc[:, 'CoEng_st'] = df['CoEng_st'].apply(lambda x: x.decode('utf-8'))
    return df


def retIODF(test_area: str) -> List[str]:
    if 'I_A_APP1' == test_area:
        columns_to_include = ['APP_uRaw1unLim', 'DFC_st.DFC_SRCHighAPP1', 'DFC_st.DFC_SRCLowAPP1', 'APP_uRaw1',
                              'APP_uRaw1SRCHigh_C', 'APP_uRaw1SRCLow_C', 'APP_uRaw1Def_C']
    return columns_to_include


def find_columns_with_dfc_err_type(draw_fault_detection_df: DataFrame, dfc_err_type: str) -> str:
    # 获取所有以'DFES_numDFC_'开头的列名
    dfc_columns = [col for col in draw_fault_detection_df.columns if col.startswith('DFES_numDFC_')]

    # 创建一个字典来存储结果，键是列名，值是布尔值
    result = {col: draw_fault_detection_df[col].str.contains(dfc_err_type, na=False).any() for col in dfc_columns}

    # 返回包含目标字符串的那些列名
    return [col for col, match in result.items() if match]


def check_row_for_dfc_err(row: pd.Series, dfc_err_type: str) -> List[str]:
    # 获取所有以'DFES_numDFC_'开头的列名
    dfc_columns = [col for col in row.index if col.startswith('DFES_numDFC_')]

    # 检查这一行中哪些列包含指定的错误类型
    result = {col: isinstance(row[col], str) and dfc_err_type in row[col] for col in dfc_columns}

    # 返回包含目标字符串的那些列名
    return [col for col, match in result.items() if match]


"""
 检查给定DataFrame中指定列是否包含以'DFC_BrkNpl'开头的字符串。

 参数:
     df (pd.DataFrame): 包含要检查的列的DataFrame。

 返回:
     bool: 如果所有指定列都不包含以'DFC_BrkNpl'开头的字符串则返回True，否则返回False。
 """


def err_type_contains_strings(df: DataFrame, specified_str: str):
    # 动态生成列名列表
    columns_to_check = [f"DFES_numDFC_[{i}]" for i in range(10)]

    # 遍历每一列并检查是否存在以'DFC_BrkNpl'开头的字符串
    for column in columns_to_check:
        if df[column].str.startswith(specified_str).any():
            return False

    return True
