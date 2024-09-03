#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

try:
    # 尝试执行可能会抛出异常的代码
    result = 10 / int(input("Enter a number: "))
    a = 10
    print(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")