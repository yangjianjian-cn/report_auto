__coding__ = "utf-8"

import logging
from contextlib import closing
from typing import Mapping

import pandas as pd
from pandas import DataFrame

from app import connectionPool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def map_dtype_to_mysql(dtype):
    """将 Pandas 数据类型映射到 MySQL 数据类型"""
    if dtype.name == 'int64':
        return 'INT'
    elif dtype.name == 'float64':
        return 'DOUBLE'
    elif dtype.name == 'float32':
        return 'FLOAT'
    elif dtype.name == 'bool':
        return 'BOOLEAN'
    elif dtype.name == 'datetime64[ns]':
        return 'DATETIME'
    elif dtype.name == 'object':
        return 'VARCHAR(255)'  # 对于字符串类型，默认长度为255
    else:
        raise ValueError(f"Unsupported data type: {dtype.name}")


"""
创建表
"""


def create_table(table_name, df) -> str:
    ret_msg = 'success'
    connection = connectionPool.get_connection()
    try:
        # 使用上下文管理器管理游标
        with connection.cursor() as cursor:
            # 检查表是否存在
            check_table_query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s AND table_schema = DATABASE()"
            # 执行建表语句
            cursor.execute(check_table_query, (table_name,))
            table_exists = cursor.fetchone()[0] > 0
            logging.info(f"Table '{table_name}' exists: {table_exists}")

            if not table_exists:
                # 创建表结构
                dynamic_part = ', '.join([f'{col} {map_dtype_to_mysql(df[col].dtype)}' for col in df.columns])
                static_part = ' file_id    int  comment "file serial number" '
                columns_info = f'{static_part},\n{dynamic_part}'

                create_table_query = f"CREATE TABLE {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, {columns_info})"
                logging.info(f"Create table query:{create_table_query}")

                cursor.execute(create_table_query)
                logging.info(f"Table '{table_name}' created successfully.")
    except Exception as e:
        logging.error(f"Failed to create table '{table_name}': {e}")
        # 回滚事务（虽然建表不需要提交，但为了保持一致性，这里还是保留）
        connection.rollback()
        ret_msg = f'{e}'

    finally:
        # 在 finally 块中归还连接
        connectionPool.release_connection(connection)

    return ret_msg


def insert_data(table_name, params: dict):
    # 构建插入SQL语句
    placeholders = ', '.join(['%s'] * len(params))
    columns = ', '.join(params.keys())
    insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    logging.info(f"insert_sql: {insert_sql}")

    # 默认值
    last_id = None
    ret_msg = ''

    connection = connectionPool.get_connection()
    try:
        with closing(connection.cursor()) as cursor:
            cursor.execute(insert_sql, list(params.values()))
            last_id = cursor.lastrowid
            connection.commit()
            ret_msg = ('success', last_id)
    except Exception as e:
        connection.rollback()
        logging.error(f"An error occurred during data insertion: {str(e)}")
        ret_msg = (str(e), last_id)
    finally:
        connectionPool.release_connection(connection)

    return ret_msg


"""
批量插入
"""


def batch_insert_data(table_name, df: DataFrame, params, batch_size=1000) -> str:
    ret_msg = 'success'
    connection = connectionPool.get_connection()
    try:

        # 获取DataFrame的所有列
        all_columns = df.columns.tolist()

        # 定义不需要更新的时间戳列
        timestamp_columns = ['timestamps']

        # 获取需要插入的列
        i_columns = all_columns
        if params is not None and len(params) > 0:
            static_columns = list(params.keys())
            i_columns.extend(static_columns)

        # 获取需要更新的列（移除时间戳列）
        u_columns = [col for col in all_columns if col not in timestamp_columns]

        # 动态构建插入语句
        insert_clauses = ', '.join(i_columns)
        insert_placeholders = ', '.join(['%s'] * len(i_columns))
        logging.debug(f"insert_clauses:{insert_clauses}")
        logging.debug(f"insert_placeholders:{insert_placeholders}")

        # 动态构建更新语句
        update_clauses = ', '.join([f"{col}=VALUES({col})" for col in u_columns])
        logging.debug(f"insert_placeholders:{update_clauses}")

        # 动态插入语句
        insert_query = f"""
            INSERT INTO {table_name} ({insert_clauses})
            VALUES ({insert_placeholders})
            ON DUPLICATE KEY UPDATE 
            {update_clauses}
        """
        logging.info(f'insert_query_sql: {insert_query}')

        df_rows = len(df)
        logging.info(f'批量插入:{df_rows}')
        start = 0
        while start < df_rows:
            end = min(start + batch_size, df_rows)
            data_batch = df.loc[start:end].values.tolist()
            logging.info(f"start={start},end={end}")

            # 添加params中的值到每个数据行中，如果存在的话
            if params is not None and len(params) > 0:
                data_batch = [[*row, *list(params.values())] for row in data_batch]

            with connection.cursor() as cursor:
                cursor.executemany(insert_query, data_batch)
                # 提交事务
                connection.commit()

            start = end
    except Exception as e:
        connection.rollback()
        logging.error(f"An error occurred: {e}")
        ret_msg = f'{e}'
    finally:
        # 关闭游标和连接
        connectionPool.release_connection(connection)
    return ret_msg


"""
检索表中字段
columns:多个字段以逗号分割
"""


def query_table_sampling(columns: str, file_ids_str_for_query: str):
    connection = connectionPool.get_connection()
    try:
        sql_query = f"""
            SELECT {columns}
            FROM (SELECT {columns}
                         ,ROW_NUMBER() OVER (ORDER BY timestamps) AS row_num
                  FROM chip_temperature
                  WHERE file_id in ({file_ids_str_for_query}) ) AS t
            WHERE row_num % 1000 = 0
            ORDER BY timestamps
        """
        logging.info(f"sql_query:{sql_query}")

        # 使用连接执行SQL语句并获取结果
        with connection.cursor() as cursor:
            cursor.execute(sql_query)

            # 获取查询结果
            results = cursor.fetchall()
            if not results or results == [(None,)]:
                return []

            # 获取列名
            column_names = [desc[0] for desc in cursor.description]
            # 将结果转换为包含字典的列表
            result_dicts = [dict(zip(column_names, row)) for row in results]

            return result_dicts
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        connectionPool.release_connection(connection)


def query_table(table_name: str, columns: str, where: str):
    connection = connectionPool.get_connection()
    try:
        sql_query = f"SELECT {columns} FROM {table_name}"
        if where:
            sql_query = sql_query + where
        logging.info(f"sql_query:{sql_query}")

        # 使用连接执行SQL语句并获取结果
        with connection.cursor() as cursor:
            cursor.execute(sql_query)

            # 获取查询结果
            results = cursor.fetchall()
            if not results or results == [(None,)]:
                return []

            # 获取列名
            column_names = [desc[0] for desc in cursor.description]
            # 将结果转换为包含字典的列表
            result_dicts = [dict(zip(column_names, row)) for row in results]

            return result_dicts
    finally:
        connectionPool.release_connection(connection)


'''
物理删除物理表中的数据
'''


def delete_from_tables(primary_table_name: str, second_table_name: str, primary_param: [str, int],
                       second_param: Mapping[str, int]):
    connection = connectionPool.get_connection()
    try:
        # 删除第一个表中的数据
        sql_delete_primary = build_delete_query(primary_table_name, primary_param)
        logging.debug(f"sql_delete_primary: {sql_delete_primary}")

        with connection.cursor() as cursor:
            cursor.execute(sql_delete_primary, list(primary_param.values()))
            logging.info(f"Deleted {cursor.rowcount} rows from {primary_table_name}")

        # 删除第二个表中的数据
        sql_delete_second = build_delete_query(second_table_name, second_param)
        logging.debug(f"sql_delete_second: {sql_delete_second}")

        with connection.cursor() as cursor:
            cursor.execute(sql_delete_second, list(second_param.values()))
            logging.info(f"Deleted {cursor.rowcount} rows from {second_table_name}")

        # 提交事务
        connection.commit()
        return True, "Deletion successful"
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        connection.rollback()  # 回滚事务
        return False, str(e)
    finally:
        connectionPool.release_connection(connection)


def build_delete_query(table_name: str, param: Mapping[str, int]) -> str:
    conditions = []
    params_list = []
    for key, value in param.items():
        conditions.append(f"{key} = %s")
        params_list.append(value)

    sql_delete = f"DELETE FROM {table_name} WHERE {' AND '.join(conditions)}"
    return sql_delete


"""
通过SQL语句查询表
"""


def query_table_by_sql(query_sql: str) -> DataFrame:
    connection = connectionPool.get_connection()
    try:
        # 使用连接执行SQL语句并获取结果
        with connection.cursor() as cursor:
            cursor.execute(query_sql)

            # 获取查询结果
            results = cursor.fetchall()
            if not results or results == [(None,)]:
                return []

            # 获取列名
            column_names = [desc[0] for desc in cursor.description]

            # 将结果转换为DataFrame
            results_df = pd.DataFrame(results, columns=column_names)
            return results_df
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.error("Traceback:", exc_info=True)
    finally:
        connectionPool.release_connection(connection)
