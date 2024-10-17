#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

import numpy as np

'''数字x除以1000，结果截取小数点后一位'''


def truncate_to_one_decimal_place(x) -> float:
    # 将数字转换为字符串，并确保它至少有一位小数
    s = f"{x / 1000:.2f}"
    # 截取小数点后的一位数字
    truncated = float(s[:s.index('.') + 2])
    return truncated


'''10进制的第4位'''


def getBit4(decimal_number: np.float64) -> str:
    # 取整数部分
    integer_part = int(np.floor(decimal_number))

    # 将整数部分转换为二进制并去除前缀 '0b'
    binary_representation = bin(integer_part)[2:]

    # 如果二进制表示不足5位，则补0
    binary_representation = binary_representation.zfill(5)

    # 获取第5位的值（从右到左计数）
    fifth_bit = binary_representation[-5]

    return str(fifth_bit)


'''10进制的第2位'''


def getBit2(decimal_number: np.float64) -> str:
    # 取整数部分
    integer_part = int(np.floor(decimal_number))

    # 将整数部分转换为二进制并去除前缀 '0b'
    binary_representation = bin(integer_part)[2:]

    # 如果二进制表示不足3位，则补0
    binary_representation = binary_representation.zfill(3)

    # 获取第2位的值（从右到左计数）
    second_bit = binary_representation[-3]

    return str(second_bit)


def getBit0(decimal_number: int) -> str:
    # 将十进制数转换为二进制字符串，并去掉前缀 "0b"
    binary_string = bin(decimal_number)[2:]

    # 返回二进制字符串的最低位（即最后一位）
    return binary_string[-1]


'''相对差值'''


def relative_difference_chip(num1: float, num2: float) -> int:
    if num2 is None:
        num2 = 0

    r_num = (num1 - num2) / num1
    r_num_percentage = round(r_num * 100, 2)
    return int(r_num_percentage)


'''
差值
'''


def difference_chip(num1: float, num2: float) -> int:
    if num2 is None:
        num2 = 0
    r_num = (num1 - num2)
    return int(r_num)