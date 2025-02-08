import os
import logging
import time
import pymysql
from dbutils.pooled_db import PooledDB

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DatabasePool:
    def __init__(self, max_connections=60, min_cached=20, max_cached=20, max_shared=0, retry_attempts=3,
                 retry_delay=5, **db_config):
        self.max_connections = max_connections
        self.min_cached = min_cached
        self.max_cached = max_cached
        self.max_shared = max_shared
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.db_config = db_config
        logging.info("db_config:%s", db_config)
        self.pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        attempt = 0
        while attempt < self.retry_attempts:
            try:
                self.pool = PooledDB(
                    creator=pymysql,
                    maxconnections=self.max_connections,
                    mincached=self.min_cached,
                    maxcached=self.max_cached,
                    maxshared=self.max_shared,
                    blocking=True,
                    maxusage=None,
                    setsession=[],
                    ping=2,
                    **self.db_config
                )
                self._pre_warm_connections()
                logging.info("Database pool initialized with %d initial connections", self.min_cached)
                return
            except pymysql.err.OperationalError as e:
                attempt += 1
                logging.warning(f"Attempt {attempt} failed to initialize database pool: {str(e)}")
                if attempt >= self.retry_attempts:
                    logging.critical("Failed to initialize database pool after multiple attempts")
                    raise
                time.sleep(self.retry_delay)

    def _pre_warm_connections(self):
        for _ in range(self.min_cached):
            try:
                conn = self.pool.connection()
                conn.close()
            except Exception as e:
                logging.error("Failed to pre-warm connection: %s", str(e))

    def get_connection(self):
        try:
            conn = self.pool.connection()
            logging.debug("Connection obtained from pool")
            return conn
        except Exception as e:
            logging.error("Failed to get connection from pool: %s", str(e))
            raise

    def close_pool(self):
        try:
            self.pool.close()
            logging.info("Database pool closed")
        except Exception as e:
            logging.error("Failed to close database pool: %s", str(e))


class TestDatabaseConnectivity:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    def test_connectivity(self):
        """
        测试数据库连通性
        """
        try:
            # 从连接池获取一个连接
            conn = self.db_pool.get_connection()
            logging.info("Successfully obtained a connection from the pool")

            try:
                # 创建游标对象
                with conn.cursor() as cursor:
                    # 执行一条简单查询
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()
                    logging.info("Database version: %s", version)
            finally:
                # 关闭连接，实际上只是将连接返回到连接池
                conn.close()
                logging.debug("Connection returned to pool")
            return True
        except Exception as e:
            logging.error("Failed to connect to database: %s", str(e))
            return False


if __name__ == "__main__":
    # 数据库配置
    mysql_config = {
        'host': 'report_db',
        'user': 'ba',
        'port': 3306,
        'password': '1qazxsw2',
        'database': 'measurement',
        'charset': 'utf8mb4'
    }
    # 初始化数据库连接池
    db_pool = DatabasePool(max_connections=20, min_cached=6, max_cached=10, max_shared=0, **mysql_config)

    # 实例化测试类并进行测试
    tester = TestDatabaseConnectivity(db_pool)
    if tester.test_connectivity():
        logging.info("Database connectivity test passed.")
    else:
        logging.error("Database connectivity test failed.")
