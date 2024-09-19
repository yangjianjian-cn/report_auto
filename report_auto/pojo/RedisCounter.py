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

    def get_value(self, key_name):
        """获取计数器当前的值"""
        value = self.r.get(key_name)
        return value.decode('utf-8') if value else 0

    def del_key(self, key):
        """删除Redis中存在的键值"""
        self.r.delete(key)
