__coding__ = "utf-8"

import os

from dotenv import load_dotenv

load_dotenv()
env_input_path = os.getenv('input_path')
env_output_path = os.getenv('output_path')
env_template_path = os.getenv('template_path')

from tools.utils.ConnectionUtils import DatabasePool

# jdbc_mysql=10.0.4.14:ba:3306:1qazxsw2:measurement
# jdbc_mysql=sh-cynosdbmysql-grp-rykty3lm.sql.tencentcdb.com:ba:26338:1qazxsw2:measurement

# 创建全局数据库连接池实例
jdbc_mysql: str = os.getenv('jdbc_mysql')
jdbc_mysql_arr = jdbc_mysql.split(":")
mysql_config = {
    'host': jdbc_mysql_arr[0],
    'user': jdbc_mysql_arr[1],
    'port': int(jdbc_mysql_arr[2]),
    'password': jdbc_mysql_arr[3],
    'database': jdbc_mysql_arr[4],
    'charset': 'utf8mb4'
}
# mysql_config = {
#     'host': os.getenv('MYSQL_HOST'),
#     'user': os.getenv('MYSQL_USER'),
#     'port': int(os.getenv('MYSQL_PORT')),
#     'password': os.getenv('MYSQL_PASSWORD'),
#     'database': os.getenv('MYSQL_DATABASE'),
#     'charset': 'utf8mb4'
# }
db_pool = DatabasePool(max_connections=20, min_cached=6, max_cached=10, max_shared=0, **mysql_config)
