#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

from pojo.RedisCounter import RedisCounter


def getRedisConnector(redis_connector: str) -> RedisCounter:
    redis_connectors = redis_connector.split(":")
    ip = redis_connectors[0]
    port = redis_connectors[1]
    passwd = redis_connectors[2]
    db = redis_connectors[3]
    redis_counter = RedisCounter(host=ip, port=port, password=passwd, db=db)
    return redis_counter
