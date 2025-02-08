__coding__ = "utf-8"

import os

from dotenv import load_dotenv

load_dotenv()
env_input_path = os.getenv('input_path')
env_output_path = os.getenv('output_path')
env_template_path = os.getenv('template_path')

from tools.utils.ConnectionUtils import DatabasePool
mysql_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'port': int(os.getenv('MYSQL_PORT')),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'charset': 'utf8mb4'
}
db_pool = DatabasePool(max_connections=20, min_cached=6, max_cached=10, max_shared=0, **mysql_config)
