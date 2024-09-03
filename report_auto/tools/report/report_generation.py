import logging

import pandas as pd
from pandas import DataFrame

from constant.faultType import FAULT_TYPE_MAPPING
from pojo.MSTReqPOJO import ReqPOJO
from tools.utils.FileUtils import delete_file

pd.set_option('future.no_silent_downcasting', True)

import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')  # TkAgg 或者 'Qt5Agg'

from docx import Document
from docx.shared import Inches

from tools.common.report_common import replace_placeholders_in_docx
from tools.common.dat_csv_common import create_file_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# 检查columns中每一列是否包含特定的fault_type值
def check_fault_type(df, columns, fault_type):
    # 创建一个空列表来存储包含故障类型的列
    columns_with_fault_type = []

    # 遍历指定的列
    for column in columns:
        # 检查该列是否包含给定的 fault_type
        if df[column].isin([fault_type]).any():
            columns_with_fault_type.append(column)

    return columns_with_fault_type


def replace_placeholders_in_boa_tables(doc, replacements):
    # 处理表格
    replace_placeholders_in_docx(doc, replacements)


def get_signals(fault_detection_df: DataFrame, docTemplateName: str, signals: list):
    # 1.异常信息缓存列，字符串替换成数值
    fault_type: str = FAULT_TYPE_MAPPING.get(docTemplateName)
    fault_type_column: str = f"DFC_st.{fault_type}"

    # 保存异常信息的列
    columns_to_replace = [
        'DFES_numDFC_[0]', 'DFES_numDFC_[1]', 'DFES_numDFC_[2]', 'DFES_numDFC_[3]',
        'DFES_numDFC_[4]', 'DFES_numDFC_[5]', 'DFES_numDFC_[6]', 'DFES_numDFC_[7]',
        'DFES_numDFC_[8]', 'DFES_numDFC_[9]'
    ]
    columns_with_faults = check_fault_type(fault_detection_df, columns_to_replace, fault_type)
    dfes_numdfc_column = columns_with_faults[0]
    logging.info(f"异常信息列:{dfes_numdfc_column}")

    # 异常信息列值替换
    # fault_detection_df[dfes_numdfc_column] = fault_detection_df[fault_type_column]
    fault_detection_df.loc[:, dfes_numdfc_column] = fault_detection_df[fault_type_column]

    # 绘制每个信号
    signals = signals + columns_with_faults
    logging.info(f"信号列:{signals}")
    return signals, fault_detection_df


def draw_img_in_boa_doc(fault_detection_df, img_output_path: str, docTemplateName: str, signals: list) -> str:
    signals, fault_detection_df = get_signals(fault_detection_df, docTemplateName, signals)

    # 3. 绘制二维坐标轴
    # ##创建一个新的图形
    fig, ax = plt.subplots(figsize=(8, 4))  # 10,6

    for signal in signals:
        ax.plot(fault_detection_df['timestamps'], fault_detection_df[signal], label=signal)

    # ##添加图例
    ax.legend()

    # ##设置图表标题和轴标签
    ax.set_title('Signals Over Time')
    ax.set_xlabel('Timestamps(s)')
    ax.set_ylabel('Signal Value')

    # 4. 保存图表到文件
    plt.tight_layout()
    plt.savefig(img_output_path)
    plt.close()
    return img_output_path


"""
replacements:占位符及其对应值
fault_detection_df: 故障集
docTemplate: 模板名称
"""


def replace_variables_in_doc(replacements, fault_detection_df, signals: list, req_data: ReqPOJO) -> str:

    template_file_name, template_path = create_file_path(req_data.template_name, 'docx', req_data.template_path,'template')
    img_name, img_path = create_file_path(req_data.template_name, 'png', req_data.output_path, 'img')
    doc_name, output_path = create_file_path(req_data.doc_output_name, 'docx', req_data.output_path, 'docx')

    draw_img_in_boa_doc(fault_detection_df, img_path, req_data.template_name, signals)
    print("图片路径:", img_path)

    # 加载模板文档
    doc = Document(template_path)
    print("模板路径:", template_path)

    # 替换表格中的占位符
    replace_placeholders_in_boa_tables(doc, replacements)

    # 插入图片
    doc.add_picture(img_path, width=Inches(6), height=Inches(4))

    # 保存输出文档
    doc.save(output_path)
    print("文档路径:", output_path)

    # 删除临时文件，释放磁盘空间
    delete_file(req_data.csv_path)
    delete_file(img_path)
    return output_path
