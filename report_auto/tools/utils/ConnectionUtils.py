import logging

import pymysql
from dbutils.pooled_db import PooledDB

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DatabasePool:
    def __init__(self, max_connections=60, min_cached=20, max_cached=20, max_shared=0, **db_config):
        """
        初始化数据库连接池
        :param max_connections: 最大连接数
        :param min_cached: 初始化时，连接池中最小的连接数
        :param max_cached: 连接池中最多闲置的连接数
        :param max_shared: 连接池中最多共享的连接数
        :param db_config: 数据库连接配置
        """
        self.max_connections = max_connections
        self.min_cached = min_cached
        self.max_cached = max_cached
        self.max_shared = max_shared
        self.db_config = db_config

        self.pool = PooledDB(
            creator=pymysql,  # 使用 pymysql 模块
            maxconnections=self.max_connections,  # 最大连接数
            mincached=self.min_cached,  # 初始化时，链接池至少创建的空闲的链接
            maxcached=self.max_cached,  # 链接池中最多闲置的链接
            maxshared=self.max_shared,  # 链接池中最多共享的链接数量
            blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，报错。
            maxusage=None,  # 一个链接最多被重复使用的次数，None 表示无限制
            setsession=[],  # 开始会话前执行的命令列表
            ping=2,  # ping MySQL 服务端，检查是否服务可用。2 表示在每次从池中获取连接时检查连接的有效性
            **self.db_config  # 数据库连接配置
        )
        self._pre_warm_connections()
        logging.info("Database pool initialized with %d initial connections", self.min_cached)

    def _pre_warm_connections(self):
        """
        预热连接池，提前建立好连接
        """
        for _ in range(self.min_cached):
            try:
                conn = self.pool.connection()
                conn.close()
            except Exception as e:
                logging.error("Failed to pre-warm connection: %s", str(e))

    def get_connection(self):
        """
        获取数据库连接
        :return: 数据库连接对象
        """
        try:
            conn = self.pool.connection()
            logging.debug("Connection obtained from pool")
            return conn
        except Exception as e:
            logging.error("Failed to get connection from pool: %s", str(e))
            raise

    def close_pool(self):
        """
        关闭连接池
        """
        try:
            self.pool.close()
            logging.info("Database pool closed")
        except Exception as e:
            logging.error("Failed to close database pool: %s", str(e))

    def get_pool_status(self):
        """
        获取连接池的状态信息
        :return: 连接池的状态信息
        """
        status = {
            'max_connections': self.max_connections,
            'min_cached': self.min_cached,
            'max_cached': self.max_cached,
            'max_shared': self.max_shared,
            'current_connections': len(self.pool._connections),
            'idle_connections': len(self.pool._idle_cache),
            'shared_connections': len(self.pool._shared_cache),
            'blocked': self.pool._blocking
        }
        return status

    @staticmethod
    def with_connection(func):
        """
        装饰器，用于自动管理连接
        :param func: 需要装饰的函数
        :return: 装饰后的函数
        """

        def wrapper(*args, **kwargs):
            db_pool = args[0]  # 假设第一个参数是 DatabasePool 实例
            conn = None
            try:
                conn = db_pool.get_connection()
                kwargs['conn'] = conn  # 将连接传递给被装饰的函数
                result = func(*args[1:], **kwargs)  # 注意这里跳过了第一个参数
                return result
            except Exception as e:
                logging.error("Error executing function with connection: %s", str(e))
                raise
            finally:
                if conn:
                    conn.close()

        return wrapper
