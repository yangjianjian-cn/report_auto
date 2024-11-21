__coding__ = "utf-8"

import logging
from typing import Mapping, Dict, List

import pandas as pd
from pandas import DataFrame

from app import db_pool

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


@db_pool.with_connection
def create_table(table_name, df: DataFrame, conn=None) -> str:
    ret_msg = 'success'
    cursor = conn.cursor()
    try:
        # 检查表是否存在
        check_table_query = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"
        # 执行建表语句
        cursor.execute(check_table_query, ('measurement', table_name))
        # 获取所有列名
        columns = [column[0] for column in cursor.fetchall()]

        if len(columns) == 0:
            # 创建表结构
            dynamic_part = ', '.join([f'{col} {map_dtype_to_mysql(df[col].dtype)}' for col in df.columns])
            static_part = ' file_id  int, source varchar(8),timestamps double '
            columns_info = f'{static_part},\n{dynamic_part}'

            create_table_query = f"CREATE TABLE {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, {columns_info})"
            logging.info(f"Create table query:{create_table_query}")

            cursor.execute(create_table_query)
            logging.info(f"Table '{table_name}' created successfully.")
    except Exception as e:
        logging.error(f"Failed to create table '{table_name}': {e}")
        # 回滚事务（虽然建表不需要提交，但为了保持一致性，这里还是保留）
        conn.rollback()
        ret_msg = f'{e}', None

    finally:
        # 在 finally 块中归还连接
        cursor.close()
    return ret_msg, columns


@db_pool.with_connection
def insert_data(table_name, params: dict, conn=None):
    logging.info(f'table_name:{table_name}')
    logging.info(f'params:{params}')

    # 构建插入SQL语句
    placeholders = ', '.join(['%s'] * len(params))
    columns = ', '.join(params.keys())
    insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    logging.info(f"insert_sql: {insert_sql}")

    # 默认值
    last_id = None

    cursor = conn.cursor()
    try:
        cursor.execute(insert_sql, list(params.values()))
        last_id = cursor.lastrowid
        conn.commit()
        ret_msg = ('success', last_id)
    except Exception as e:
        conn.rollback()
        logging.error(f"An error occurred during data insertion: {str(e)}")
        ret_msg = (str(e), last_id)
    finally:
        cursor.close()

    return ret_msg


"""
批量插入
"""


@db_pool.with_connection
def batch_insert_data(table_name: str, params: Dict, df: pd.DataFrame, batch_size: int = 5000, conn=None) -> str:
    ret_msg = 'success'
    cursor = conn.cursor()
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
        i_columns = i_columns + timestamp_columns

        # 获取需要更新的列（移除时间戳列）
        u_columns = [col for col in all_columns if col not in timestamp_columns]

        # 动态构建插入语句
        insert_clauses = ', '.join(i_columns)
        insert_placeholders = ', '.join(['%s'] * len(i_columns))
        logging.debug(f"insert_clauses:{insert_clauses}")
        logging.debug(f"insert_placeholders:{insert_placeholders}")
        logging.debug(f"params:{params}")

        # 动态构建更新语句
        update_clauses = ', '.join([f"{col}=VALUES({col})" for col in u_columns])
        logging.debug(f"update_placeholders:{update_clauses}")

        # 动态插入语句
        insert_query = f"""
            INSERT INTO {table_name} ({insert_clauses})
            VALUES ({insert_placeholders})
        """
        logging.info(f'insert_query_sql: {insert_query}')

        start = 0
        df_rows = len(df)
        logging.info(f'批量插入:{df_rows}')
        while start < df_rows:
            end = min(start + batch_size, df_rows)
            data_batch = df.iloc[start:end].copy()
            logging.info(f"start={start},end={end},len:{len(data_batch)}")

            # 添加params中的值到每个数据行中，如果存在的话
            if params is not None and len(params) > 0:
                for key, value in params.items():
                    if type(value) is float:
                        data_batch[key] = value.round(3)
                    else:
                        data_batch[key] = value

            data_batch['timestamps'] = data_batch.index
            data_batch = data_batch[i_columns].values.tolist()

            # 添加params中的值到每个数据行中，如果存在的话
            cursor.executemany(insert_query, data_batch)
            # 提交事务
            conn.commit()

            start = end
    except Exception as e:
        conn.rollback()
        logging.error(f"An error occurred: {e}")
        ret_msg = f'{e}'
    finally:
        # 关闭游标
        cursor.close()
    return ret_msg


"""
检索表中字段
columns:多个字段以逗号分割
"""


@db_pool.with_connection
def query_table_sampling(columns: str, file_ids_str_for_query: str, conn=None, measurement_source=None):
    cursor = conn.cursor()
    try:
        sql_query = f"""
            SELECT {columns}
            FROM (SELECT {columns}
                         ,ROW_NUMBER() OVER (ORDER BY timestamps) AS row_num
                  FROM chip_temperature
                  WHERE file_id in ({file_ids_str_for_query}) and source='{measurement_source}') AS t
            WHERE row_num % 1000 = 0
            ORDER BY timestamps
        """
        logging.info(f"sql_query:{sql_query}")

        # 使用连接执行SQL语句并获取结果
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
        cursor.close()


@db_pool.with_connection
def query_table(query=None, params=None, conn=None):
    logging.info(f"query_sql:{query}")
    logging.info(f"query_params:{params}")
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
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
        # 记录异常信息
        logging.error(f"An error occurred: {e}")
        # 可以选择回滚事务（如果需要）
        if conn:
            conn.rollback()
        # 返回空列表或其他默认值，或者抛出异常
        return []
    finally:
        # 关闭游标
        cursor.close()


'''
物理删除物理表中的数据
'''


@db_pool.with_connection
def delete_from_tables(table: str, param: Mapping[str, int], conn=None):
    cursor = conn.cursor()
    try:
        # 删除第一个表中的数据
        sql_delete_primary = build_delete_query(table, param)
        logging.debug(f"sql_delete_primary: {sql_delete_primary}")

        cursor.execute(sql_delete_primary, list(param.values()))
        logging.info(f"Deleted {cursor.rowcount} rows from {table}")
        # 提交事务
        conn.commit()
        return True, "Deletion successful"
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        conn.rollback()  # 回滚事务
        return False, str(e)
    finally:
        cursor.close()


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


@db_pool.with_connection
def query_table_by_sql(query_sql: str, conn=None) -> DataFrame:
    cursor = conn.cursor()
    try:
        # 使用连接执行SQL语句并获取结果
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
        cursor.close()


@db_pool.with_connection
def update_table(table: str, set_params: Mapping[str, any], where_params: Mapping[str, any], conn=None):
    cursor = conn.cursor()
    try:
        # 构建更新SQL语句
        columns_set = ', '.join([f"{k}=%s" for k in set_params.keys()])
        columns_where = ' AND '.join([f"{k}=%s" for k in where_params.keys()])
        sql_update = f"UPDATE {table} SET {columns_set} WHERE {columns_where}"
        logging.debug(f"sql_update: {sql_update}")

        # 执行更新操作
        values = list(set_params.values()) + list(where_params.values())
        cursor.execute(sql_update, values)
        logging.info(f"Updated {cursor.rowcount} rows in {table}")

        # 提交事务
        conn.commit()
        return True, "Update successful"
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        conn.rollback()  # 回滚事务
        return False, str(e)
    finally:
        cursor.close()


@db_pool.with_connection
def alter_table_add_columns(table: str, columns: List[str], column_type: str, conn=None):
    cursor = conn.cursor()
    try:
        # 构建 ALTER TABLE 语句
        alter_statements = [f"ALTER TABLE {table} ADD COLUMN {column} {column_type};" for column in columns]

        # 执行所有 ALTER TABLE 语句
        for statement in alter_statements:
            logging.debug(f"Executing: {statement}")
            cursor.execute(statement)

        # 提交事务
        conn.commit()
        logging.info(f"Added {len(columns)} columns to {table}")
        return True, "Columns added successfully"
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        conn.rollback()  # 回滚事务
        return False, str(e)
    finally:
        cursor.close()
