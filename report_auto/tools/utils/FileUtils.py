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
    elif 'IO_Test' == test_team:
        valid_filenames.update(['level-1', 'level-2', 'level-3', 'level-4', 'level2-4'])

    if len(valid_filenames) > 0:
        base_file_name = get_filename_without_extension(filename).lower()
        if base_file_name not in valid_filenames:
            return (f'文件名 {base_file_name} 不符合规定，请使用以下格式之一：{", ".join(valid_filenames)}')
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


# csv_file = r'C:\Users\Administrator\Downloads\output\HTM\csv\HTM03_idle.csv'
# subdirectory = 'dc1'
# new_csv_file = add_subdirectory_to_path(csv_file, subdirectory)
# print(new_csv_file)  # 输出: C:\Users\Administrator\Downloads\output\HTM\csv\dc1\HTM03_idle.csv
