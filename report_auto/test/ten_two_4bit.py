import numpy as np


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


# getBit4(251)
# print(getBit2(168) + ',' + getBit4(168))
# print(getBit0(65))
# print(getBit0(80))
# print(getBit0(81))
