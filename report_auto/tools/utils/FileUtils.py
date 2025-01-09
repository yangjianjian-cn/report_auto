#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

import logging
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def delete_file(file_path) -> bool:
    # 检查文件是否存在
    if os.path.exists(file_path):
        # 尝试删除文件
        try:
            os.remove(file_path)
            logging.info(f"文件 {file_path} 删除成功。")
            return True
        except Exception as e:
            logging.error(f"删除文件 {file_path} 时发生错误：{e}")
            return False
    else:
        logging.error(f"文件 {file_path} 不存在。")
        return False


def get_filename_with_extension(file_path):
    # 使用os.path.basename()获取文件名（包括扩展名）
    return os.path.basename(file_path)


def get_filename_without_extension(file_path) -> str:
    # 使用os.path.splitext()分割文件名和扩展名
    file_name, _ = os.path.splitext(os.path.basename(file_path))
    return file_name


def validate_filename(filename: str, test_team: str) -> str:
    valid_filenames = set()

    if 'MST_Test' == test_team:
        valid_filenames.update(['app_pl_br_1', 'brk_04', 'brk_05', 'ngs_06', 'clth_05', 'clth_06'])
    # elif 'IO_Test' == test_team:
    #     valid_filenames.update(['level1', 'level2', 'level3', 'level4', 'level2-4'])

    if len(valid_filenames) > 0:
        base_file_name = get_filename_without_extension(filename).lower()
        if base_file_name not in valid_filenames:
            return (
                f'The file name {base_file_name} does not conform to the regulations, please use one of the following formats：{", ".join(valid_filenames)}')
    return ''  # 或


def add_subdirectory_to_path(file_path, subdirectory):
    # 分离文件路径中的目录和文件名
    base_dir, file_name = os.path.split(file_path)

    # 分离目录中的子目录和目标子目录
    new_dir = os.path.join(base_dir, subdirectory)

    # 如果子目录不存在，则创建它
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)

    # 组合新的文件路径
    new_file_path = os.path.join(new_dir, file_name)

    return new_file_path


from docx import Document
from docxcompose.composer import Composer
from docx.enum.text import WD_BREAK


def merge_docs(output_path, input_paths):
    # 初始化第一个文档作为主文档
    master = Document(input_paths[0])
    composer = Composer(master)

    # 循环合并剩余的文档
    for input_path in input_paths[1:]:
        # 打开每个输入文档
        doc = Document(input_path)

        # 在每个新文档前插入一个分页符
        add_page_break(master)

        # 将当前文档添加到主文档中
        composer.append(doc)

    # 保存合并后的文档到指定路径
    composer.save(output_path)


def add_page_break(doc):
    # 创建一个段落并添加分页符
    paragraph = doc.add_paragraph()
    run = paragraph.add_run()
    run.add_break(WD_BREAK.PAGE)  # 插入分页符


def insert_string_before_extension(filename, insert_str, delimiter='.'):
    """
    在给定文件名的扩展名前插入指定字符串。

    参数:
        filename (str): 原始文件名。
        insert_str (str): 要在文件名扩展名前插入的字符串。
        delimiter (str): 用于分割文件名和扩展名的字符，默认为点号 ('.')。

    返回:
        str: 修改后的文件名。
    """
    # 分离文件名和扩展名
    name_part, ext_part = filename.rsplit('.', 1)

    # 在文件名与扩展名之间插入字符串
    new_filename = f"{name_part}{delimiter}{insert_str}{'.'}{ext_part}"

    return new_filename


def extract_prefix(file_path: str):
    # 去掉文件扩展名
    base_name = os.path.splitext(file_path)[0]

    # 按照路径分隔符来切分，取文件名部分
    file_name = os.path.basename(base_name)

    return file_name


def get_folder_path(file_path):
    # 去掉路径末尾的斜杠（如果有）
    file_path = file_path.rstrip(os.sep)

    # 使用 os.path.dirname 获取文件夹路径
    folder_path = os.path.dirname(file_path)

    # 确保路径以斜杠结尾（可选）
    if folder_path and not folder_path.endswith(os.sep):
        folder_path += os.sep

    return folder_path
