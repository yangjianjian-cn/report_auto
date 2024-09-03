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
            logging.info(f"文件 {file_path} 已被删除。")
            return True
        except Exception as e:
            logging.error(f"删除文件 {file_path} 时发生错误：{e}")
            return False
    else:
        logging.error(f"文件 {file_path} 不存在。")
        return False


# 使用函数
file_name = r'C:\Users\Administrator\Downloads\output\MST_Test\csv\1APP_PL_BR_1.csv'
success, message = delete_file(file_name)
print(message)
