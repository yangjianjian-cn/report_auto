from typing import List

from pandas import DataFrame

from constant.TestCaseType import TestCaseType

'''csv文件列名重命名'''


def reMstDF(df: DataFrame, output_file_name: str) -> DataFrame:
    # 通用特征列
    dfes_list = ['DFES_numDFC_[0]', 'DFES_numDFC_[1]', 'DFES_numDFC_[2]', 'DFES_numDFC_[3]',
                 'DFES_numDFC_[4]', 'DFES_numDFC_[5]', 'DFES_numDFC_[6]', 'DFES_numDFC_[7]', 'DFES_numDFC_[8]',
                 'DFES_numDFC_[9]']

    # 根据dat文件名称，提取特征列
    if TestCaseType.brake_override_accelerator.value in output_file_name.lower():
        need_include_column_list = ['Tra_numGear', 'VehV_v', 'APP_r', 'Epm_nEng', 'CEngDsT_t', 'Brk_stMn',
                                    'Brk_stRed', 'APP_bPlaBrk', 'APP_rUnFlt', 'Brk_st', 'DFC_st.DFC_APPPlausBrk']
        columns_to_include = need_include_column_list + dfes_list
        # 二进制字符串 b'',转换为字符串
        df = df[columns_to_include]
    elif TestCaseType.main_brake_plausibility_check.value in output_file_name.lower():
        need_include_column_list = ['Tra_numGear', 'Epm_nEng', 'Brk_stMn', 'Brk_stRed', 'DFC_st.DFC_BrkPlausChk',
                                    'DDRC_DurDeb.Brk_tiPlausChkDebDef_C', 'Brk_st']
        columns_to_include = need_include_column_list + dfes_list
        # 二进制字符串 b'',转换为字符串
        df = df[columns_to_include]
    elif TestCaseType.redundant_brake_plausibility_check.value in output_file_name.lower():
        need_include_column_list = ['Tra_numGear', 'VehV_v', 'Brk_tiMaiSwtDebHiLo_C', 'Brk_stMn', 'Brk_stRed',
                                    'Brk_st']
        columns_to_include = need_include_column_list + dfes_list
        # 二进制字符串 b'',转换为字符串
        df = df[columns_to_include]

    df.loc[:, 'Brk_stMn'] = df['Brk_stMn'].apply(lambda x: x.decode('utf-8'))
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
    return df


def retIODF(test_area: str) -> List[str]:
    if 'I_A_APP1' == test_area:
        columns_to_include = ['APP_uRaw1unLim', 'DFC_st.DFC_SRCHighAPP1', 'DFC_st.DFC_SRCLowAPP1', 'APP_uRaw1',
                              'APP_uRaw1SRCHigh_C', 'APP_uRaw1SRCLow_C', 'APP_uRaw1Def_C']
    return columns_to_include
