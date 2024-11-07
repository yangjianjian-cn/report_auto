__coding__ = "utf-8"

import logging
import os
from pathlib import Path

from app import db_pool
from constant.TestCaseType import TestCaseType
from pojo.MSTReqPOJO import ReqPOJO
from tools.conversion.iotest.analogue_input import IOTestDataInDB
from tools.conversion.iotest.levels_analysis import simple_electrical_test, error_detection, \
    error_debouncing_error_healing, substitute_value_reaction_test
from tools.report.xlsm_report_generation import analogue_input_report
from tools.utils.DBOperator import query_table
from tools.utils.xlsm_utils import find_first_empty_row_after_string

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

"""
csvPath: /outputpath/测试团队/测试场景/测试功能
outputPath：/outputpath/测试团队/测试区域
"""


def analogue_input(req_data: ReqPOJO) -> str:
    logging.info("report generation:")
    level1, level2, level3, level4 = 'n/a', 'n/a', 'n/a', 'n/a'

    csv_path = req_data.csv_path
    output_path = req_data.output_path
    test_scenario = req_data.test_scenario
    test_area = req_data.test_area
    logging.info(f"CSV Path: {csv_path}")
    logging.info(f"Output Path: {output_path}")
    logging.info(f"Test Scenario: {test_scenario}")
    logging.info(f"Test Area: {test_area}")

    # 该引脚测试报告输出模板
    ioTestDataInDB = IOTestDataInDB()
    result_dicts = ioTestDataInDB.get_io_test_data(test_area,test_scenario)
    logging.info(f"result_dicts:{result_dicts}")

    # 输出文件
    output_file = os.path.join(output_path, "xlsm", "IOTest_Main_Tmplt.xlsm")
    logging.info(f"输出文件:{output_file}")

    insert_rownum = 0
    if os.path.exists(output_file):
        insert_rownum = find_first_empty_row_after_string(output_file, test_scenario)
    logging.info(f"insert_rownum:{insert_rownum}")

    # 测量文件
    for file_path in Path(csv_path).glob('**/*.csv'):
        logging.info(f"measurement files:{file_path}")
        file_name = file_path.name.lower()
        if "level1" in file_name:
            level1 = simple_electrical_test(file_path, result_dicts)
            logging.info(f"level1:{level1}")
        elif "level2" in file_name:
            level2 = error_detection(file_path, result_dicts)
            logging.info(f"level2:{level2}")
        elif "level3" in file_name:
            level3 = error_debouncing_error_healing(file_path, result_dicts)
            pass
        elif "level4" in file_name:
            level4 = substitute_value_reaction_test(file_path, result_dicts)
            pass

# ########## 校验level2
# req_data.template_name = TestCaseType.IOTest_Man_Tmplt.name
# xlsm_path = analogue_input_report(req_data, level1, level2, level3, level4, extracted_parts_str)
# return xlsm_path
