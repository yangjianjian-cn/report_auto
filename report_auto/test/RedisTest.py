#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

import redis

# 创建一个 Redis 连接池（可选）
# pool = redis.ConnectionPool(host='localhost', port=6379, db=0)

# 创建 Redis 连接
r = redis.Redis(host='111.231.0.147', port=6379, db=0, password='123456')

# 测试连接
try:
    r.ping()
    print("Connected to Redis server.")
except (redis.exceptions.ConnectionError) as e:
    print(f"Failed to connect to Redis: {e}")

# 示例操作：设置键值对
r.set('example_key', 'example_value')

# 获取值
value = r.get('example_key')
print(f"Retrieved value: {value.decode('utf-8')}")

# 关闭连接
# 注意：在实际应用中，Redis 连接通常保持打开状态以便重复使用
# 如果你想显式关闭连接，可以这样做：
# conn.close()
