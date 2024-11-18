__coding__ = "utf-8"

import logging
import os
from pathlib import Path

from pojo.MSTReqPOJO import ReqPOJO
from tools.conversion.iotest.analogue_input import IOTestDataInDB
from tools.conversion.iotest.analysis_tocsv import write_analysis_tocsv
from tools.conversion.iotest.levels_analysis import simple_electrical_test, high_error_debouncing_error_healing, \
    low_error_debouncing_error_healing, low_substitute_value_reaction_test, high_substitute_value_reaction_test, \
    high_error_detection, low_error_detection
from tools.utils.xlsm_utils import find_first_empty_row_after_string

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

"""
csvPath: /outputpath/测试团队/测试场景/测试功能
outputPath：/outputpath/测试团队/测试区域
"""


def analogue_input(req_data: ReqPOJO) -> str:
    logging.info("report generation: tools.conversion.iotest.analogue_input_parser.analogue_input")

    csv_path = req_data.csv_path
    output_path = req_data.output_path

    test_scenario: str = req_data.test_scenario
    test_area = req_data.test_area
    test_area_dataLabel = req_data.test_area_dataLabel

    logging.info(f"CSV Path: {csv_path}")
    logging.info(f"Output Path: {output_path}")
    logging.info(f"Test Scenario: {test_scenario}")
    logging.info(f"Test Area: {test_area}")
    logging.info(f"Test Area DataLabel: {test_area_dataLabel}")

    # 1.引脚测试报告输出模板
    ioTestDataInDB = IOTestDataInDB()
    result_dicts = ioTestDataInDB.get_io_test_data(test_area=test_area, test_scenario=test_scenario,
                                                   test_area_dataLabel=test_area_dataLabel)
    logging.info(f"result_dicts:{result_dicts}")

    # 2.分析测量文件
    level1: set[str] = set()
    level2: set[str] = set()
    level3: set[str] = set()
    level4: set[str] = set()

    for file_path in Path(csv_path).glob('**/*.csv'):
        logging.info(f"measurement files:{file_path}")
        file_name = file_path.name.lower()

        if "analogue_input" == req_data.test_scenario:
            if "level1" in file_name:
                level1_str: str = simple_electrical_test(file_path, result_dicts)
                level1.add(level1_str)
                logging.info(f"level1:{level1}")

            elif "level2_high" in file_name:
                high_level2_str: str = high_error_detection(file_path, result_dicts)
                level2.add(high_level2_str)
                logging.info(f"level2_high:{high_level2_str}")

            elif "level2_low" in file_name:
                low_level2_str: str = low_error_detection(file_path, result_dicts)
                level2.add(low_level2_str)
                logging.info(f"level2_low:{low_level2_str}")

            elif "level3_high" in file_name:
                high_deb_level3, high_ok_level3 = high_error_debouncing_error_healing(file_path, result_dicts)
                if high_deb_level3 != "":
                    level3.add(high_deb_level3)
                if high_ok_level3 != "":
                    level3.add(high_ok_level3)
                logging.info(f"level3_high:{high_deb_level3},{high_ok_level3}")

            elif "level3_low" in file_name:
                low_deb_level3, low_ok_level3 = low_error_debouncing_error_healing(file_path, result_dicts)
                if low_deb_level3 != "":
                    level3.add(low_deb_level3)
                if low_ok_level3 != "":
                    level3.add(low_ok_level3)
                logging.info(f"level3_low:{low_deb_level3},{low_ok_level3}")

            elif "level4_high" in file_name:
                high_level4 = high_substitute_value_reaction_test(file_path, result_dicts)
                level4.add(high_level4)
                logging.info(f"level4_high:{high_level4}")

            elif "level4_low" in file_name:
                low_level4 = low_substitute_value_reaction_test(file_path, result_dicts)
                level4.add(low_level4)
                logging.info(f"level4_low:{low_level4}")

            else:
                high_deb_level3, high_ok_level3 = high_error_debouncing_error_healing(file_path, result_dicts)
                low_deb_level3, low_ok_level3 = low_error_debouncing_error_healing(file_path, result_dicts)
                level3.add(high_deb_level3)
                level3.add(high_ok_level3)
                level3.add(low_deb_level3)
                level3.add(low_ok_level3)

                high_level4 = high_substitute_value_reaction_test(file_path, result_dicts)
                low_level4 = low_substitute_value_reaction_test(file_path, result_dicts)
                level4.add(high_level4)
                level4.add(low_level4)
        elif "digital_input" == req_data.test_scenario:
            pass
        elif "PWM_input" == req_data.test_scenario:
            pass
    # 3.输出文件
    output_file = os.path.join(output_path, "xlsm", "IOTest_Main_Tmplt.xlsm")
    logging.info(f"输出文件:{output_file}")

    insert_rownum = 0
    if os.path.exists(output_file):
        test_scenario = test_scenario.replace("_", " ")
        insert_rownum = find_first_empty_row_after_string(output_file, test_scenario)
    logging.info(f"insert_rownum:{insert_rownum}")

    # 4.分析结果、引脚模板、合成输出文件
    levels = {
        "level1": level1,
        "level2": level2,
        "level3": level3,
        "level4": level4,
    }
    write_analysis_tocsv(output_file, insert_rownum, levels, result_dicts)
