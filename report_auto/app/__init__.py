__coding__ = "utf-8"

import os

from dotenv import load_dotenv
from flask import Flask

from config.ChipNamesConfig import ChipNamesConfig
from tools.utils.ConnectionUtils import ConnectionPool


def create_app():
    main = Flask(__name__, template_folder='../templates', static_folder='../static')
    # 加载 .env 文件
    load_dotenv()
    # 从环境变量中读取配置
    main.config['input_path'] = os.getenv('input_path')
    main.config['output_path'] = os.getenv('output_path')
    main.config['template_path'] = os.getenv('template_path')
    # 111.231.0.147:ba:3307:1qazxsw2:measurement:5
    main.config['jdbc_mysql'] = os.getenv('jdbc_mysql')
    return main


main = create_app()

# Database connection configuration
# 111.231.0.147:ba:3307:1qazxsw2:measurement
mysql_config = {
    'host': 'sh-cynosdbmysql-grp-rykty3lm.sql.tencentcdb.com',
    'user': 'ba',
    'port': 26338,
    'password': '1qazxsw2',
    'database': 'measurement'
}
connectionPool = ConnectionPool(config=mysql_config, max_connections=30)
connectionPool.init_pool()

chipNamesConfig = ChipNamesConfig()