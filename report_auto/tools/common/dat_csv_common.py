import os

import pandas as pd
from asammdf import MDF
from docx import Document
from docx.table import Table
from docx.text.run import Run
from pathlib import Path

from constant.TestCaseType import TestCaseType

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def create_file_path(dat_file: str, output_file_name_ext: str, output_path: str, sub_dir: str):
    # 提取文件名（不包括扩展名）
    output_file_name = Path(dat_file).stem
    # 构建文件名
    target_file = f"{output_file_name}.{output_file_name_ext}"
    # 构建输出路径
    output_file_path = Path(output_path) / sub_dir / target_file
    logging.debug(f"output_file_name={output_file_name}")
    logging.debug(f"target_file={target_file}")
    logging.debug(f"output_file_path={output_file_path}")

    # 创建必要的目录
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    return output_file_name, str(output_file_path)


"""
文件转换 dat -> csv
dat_file: dat文件所在目录
outputPath: csv文件输出目录
"""


def dat_csv_conversion(dat_file: str, inputPath: str, outputPath: str) -> str:
    filepath = os.path.join(inputPath, dat_file)
    try:
        # 构建CSV输出文件路径
        # csv文件名和dat文件保持一致
        output_file_name, csv_file = create_file_path(dat_file, "csv", outputPath, "csv")

        # MDF数据转换为DataFrame
        mdf = MDF(filepath)
        df = mdf.to_dataframe()

        # 获得DataFrame对象中的所有列名,并为每一列起别名
        column_names = df.columns.tolist()
        alias_column_names = {item: item.split('\\')[0] for item in column_names}
        df.rename(columns=alias_column_names, inplace=True)

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

        df['Brk_stMn'] = df['Brk_stMn'].apply(lambda x: x.decode('utf-8'))
        df['Brk_stRed'] = df['Brk_stRed'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[0]'] = df['DFES_numDFC_[0]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[1]'] = df['DFES_numDFC_[1]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[2]'] = df['DFES_numDFC_[2]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[3]'] = df['DFES_numDFC_[3]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[4]'] = df['DFES_numDFC_[4]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[5]'] = df['DFES_numDFC_[5]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[6]'] = df['DFES_numDFC_[6]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[7]'] = df['DFES_numDFC_[7]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[8]'] = df['DFES_numDFC_[8]'].apply(lambda x: x.decode('utf-8'))
        df['DFES_numDFC_[9]'] = df['DFES_numDFC_[9]'].apply(lambda x: x.decode('utf-8'))

        # dat文件转csv文件
        df.to_csv(csv_file, index=True)
        return csv_file
    except FileNotFoundError:
        return f"err:File not found: {filepath}"
    except ValueError as ve:
        logging.error(ve)
        return f"err:Value error during conversion: {str(ve)}"
    except Exception as e:
        logging.error(e)
        return f"err:Error reading {filepath}: {str(e)}"
