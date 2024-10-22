__coding__ = "utf-8"

import os

from dotenv import load_dotenv
from flask import Flask

from config.ChipNamesConfig import ChipNamesConfig
from tools.utils.ConnectionUtils import DatabasePool

load_dotenv()

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
db_pool = DatabasePool(max_connections=60, min_cached=20, max_cached=20, max_shared=0, **mysql_config)
chipNamesConfig = ChipNamesConfig()


def create_app():
    main = Flask(__name__, template_folder='../templates', static_folder='../static')
    main.config['input_path'] = os.getenv('input_path')
    main.config['output_path'] = os.getenv('output_path')
    main.config['template_path'] = os.getenv('template_path')
    return main


main = create_app()
