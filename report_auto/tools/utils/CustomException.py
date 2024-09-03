#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"


class CustomException(Exception):
    """自定义异常类"""

    def __init__(self, message="Custom exception occurred"):
        super().__init__(message)
