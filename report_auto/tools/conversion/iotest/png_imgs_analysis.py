#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

import glob
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def pwm_input_png_fetch_dutyCycle(png_dir_path: str):
    # 记录传入的目录路径
    logging.info(f"png_dir_path: {png_dir_path}")

    # 构建PNG文件的搜索模式
    png_search_pattern = os.path.join(png_dir_path, '*.png')

    # 使用glob模块查找所有PNG文件
    png_files = glob.glob(png_search_pattern)

    # 遍历找到的PNG文件
    for png_file in png_files:
        logging.info(f"Found PNG file: {png_file}")
        # 在这里可以添加处理每个PNG文件的代码
        # 例如：读取文件、计算占空比等


# pwm_input_png_fetch_dutyCycle(png_dir_path=r'C:\Users\Administrator\Downloads\input\127001\IO_Test\PWM_input\I_F_FSS')
