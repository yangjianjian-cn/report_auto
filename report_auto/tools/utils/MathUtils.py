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
