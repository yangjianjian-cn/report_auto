__coding__ = "utf-8"

import concurrent.futures
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# jdbc_mysql=111.231.0.147:ba:3307:1qaz@WSX:measurement:5
jdbc_mysql = os.getenv('jdbc_mysql')
jdbc_arr = jdbc_mysql.split(':')
print(jdbc_arr)

# 数据库连接池配置
db_config = {
    'host': jdbc_arr[0],
    'user': jdbc_arr[1],
    'port': int(jdbc_arr[2]),
    'password': jdbc_arr[3],
    'database': jdbc_arr[4],
    'pool_name': 'measurement_pool',
    'pool_size': int(jdbc_arr[5]),  # 根据实际情况调整池大小
}

# 创建数据库连接池
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)


def get_connection():
    return connection_pool.get_connection()


def safe_query(connection, query, params=None):
    """执行SQL查询，并处理可能的异常"""
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        cursor.close()
        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        return None


def safe_execute(connection, query, params=None):
    """执行SQL命令（如插入、更新等），并提交事务"""
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        cursor.close()
    except Exception as e:
        print(f"Error executing command: {e}")
        connection.rollback()


def create(connection):
    query = "INSERT INTO your_table (column1, column2) VALUES (%s, %s)"
    params = ('value1', 'value2')
    safe_execute(connection, query, params)


def read(connection, read_sql: str):
    print(read_sql)
    # params = ('value1',)
    results = safe_query(connection, read_sql)
    print(type(results))
    for row in results:
        print(row)


def update(connection):
    query = "UPDATE your_table SET column2 = %s WHERE column1 = %s"
    params = ('new_value', 'value1')
    safe_execute(connection, query, params)


def delete(connection):
    query = "DELETE FROM your_table WHERE column1 = %s"
    params = ('value1',)
    safe_execute(connection, query, params)


def task(func, *args):
    conn = get_connection()
    try:
        func(conn, *args)
    finally:
        conn.close()  # 确保连接关闭


if __name__ == "__main__":
    # 方式1. 省略max_workers=5参数
    with concurrent.futures.ThreadPoolExecutor() as executor:
        read_sql = 'select id,chip_id,temperature,measure_time,source,is_valid from chip_temperature'
        # 提交任务到线程池
        executor.submit(task, read, read_sql)

    # 方式2.
    read_conn = get_connection()
    read(read_conn, read_sql)
