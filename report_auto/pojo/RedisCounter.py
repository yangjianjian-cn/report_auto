#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

import redis


class RedisCounter:
    def __init__(self, host='localhost', port=6379, db=0, key_name='counter', password=None):
        self.r = redis.Redis(host=host, port=port, db=db, password=password)
        self.key_name = key_name
        # 初始化计数器的值
        if not self.r.exists(self.key_name):
            self.r.set(self.key_name, 0)

    def increment(self, step=1):
        """递增计数器的值"""
        self.r.incrby(self.key_name, step)

    def get_value(self, default_value=0):
        """获取计数器当前的值"""

        value = self.r.get(self.key_name)
        return value.decode('utf-8') if value else default_value

    def get_value(self, key, default_value=0):
        """获取计数器当前的值"""

        value = self.r.get(key)
        return value.decode('utf-8') if value else default_value

# # 使用示例
# if __name__ == "__main__":
#     # 创建一个Redis计数器实例
#     counter = RedisCounter()
#
#     # 测试递增功能
#     for _ in range(5):
#         counter.increment()
#
#     # 打印当前计数器的值
#     print(f"Current counter value: {counter.get_value()}")
