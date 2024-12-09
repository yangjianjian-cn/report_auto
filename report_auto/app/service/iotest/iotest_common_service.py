import logging
from typing import List

import pandas as pd

from tools.utils.MathUtils import getBit4

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def check_row(row, result_dicts, is_high):
    measurements_1 = result_dicts[0].get("measurements_1")
    logging.debug("实时电压观测量:%s", measurements_1)

    preparation_2_str = result_dicts[0].get("preparation_2")
    preparation_2_list = preparation_2_str.splitlines()
    preparation_2_value = preparation_2_list[0 if is_high else 1]
    logging.debug("电压阈值观测量:%s", preparation_2_value)

    measurements_2_str = result_dicts[0].get("measurements_2")
    measurements_2_list = measurements_2_str.splitlines()
    measurements_2_value = measurements_2_list[0 if is_high else 1]
    logging.debug("观测状态量:%s", measurements_2_value)

    comparison = (row[measurements_1] > row[preparation_2_value]) if is_high else (
            row[measurements_1] < row[preparation_2_value])

    if comparison:
        return 'passed' if getBit4(row[measurements_2_value]) == '1' else 'failed'
    else:
        return 'not applicable'  # 当条件不满足时，返回一个特定的消息或值
