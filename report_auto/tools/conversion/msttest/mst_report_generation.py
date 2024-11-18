#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

import logging
import os

from constant.TestCaseType import TestCaseType
from pojo.MSTReqPOJO import ReqPOJO
from tools.conversion.brake_override_accelerator_parser import brake_override_accelerator
from tools.conversion.main_brake_plausibility_check_parser import main_brake_plausibility_check
from tools.conversion.mst_header_page import replace_mst_header_page_docx
from tools.conversion.neutral_gear_sensor_plausibility_parser import neutral_gear_sensor_plausibility
from tools.conversion.plausibility_check_of_clth_stuck_bottom_parser import plausibility_check_of_clth_stuck_bottom
from tools.conversion.plausibility_check_of_clth_stuck_top_parser import plausibility_check_of_clth_stuck_top
from tools.conversion.redundant_brake_plausibility_check_parser import redundant_brake_plausibility_check

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

'''csvPath: str, outputPath: str'''


def mst_report(req_data: ReqPOJO) -> str:
    logging.info(f'开始生成:{req_data.csv_path}')
    csv_file_name: str = os.path.basename(req_data.csv_path)
    logging.info(f"文件名:{csv_file_name}")

    doc_output_path = ''
    if TestCaseType.brake_override_accelerator.value in csv_file_name.lower():
        # 1.Brake_Override_Accelerator
        req_data.template_name = TestCaseType.brake_override_accelerator.name
        doc_output_path = brake_override_accelerator(req_data)

    elif TestCaseType.main_brake_plausibility_check.value in csv_file_name.lower():
        # 2Main Brake Plausibility Check (DIO)
        req_data.template_name = TestCaseType.main_brake_plausibility_check.name
        doc_output_path = main_brake_plausibility_check(req_data)

    elif TestCaseType.redundant_brake_plausibility_check.value in csv_file_name.lower():
        # 3Redundant Brake Plausibility Check (DIO)
        req_data.template_name = TestCaseType.redundant_brake_plausibility_check.name
        doc_output_path = redundant_brake_plausibility_check(req_data)

    elif TestCaseType.neutral_gear_sensor_plausibility_check.value in csv_file_name.lower():
        # 4Neutral Gear Sensor Plausibility Check (Digital Sensor)
        req_data.template_name = TestCaseType.neutral_gear_sensor_plausibility_check.name
        doc_output_path = neutral_gear_sensor_plausibility(req_data)

    elif TestCaseType.plausibility_check_of_clth_stuck_top.value in csv_file_name.lower():
        # 5Plausibility check of CLTH-stuck (Digital Sensor-Top Clutch)
        req_data.template_name = TestCaseType.plausibility_check_of_clth_stuck_top.name
        doc_output_path = plausibility_check_of_clth_stuck_top(req_data)

    elif TestCaseType.plausibility_check_of_clth_stuck_bottom.value in csv_file_name.lower():
        # 6Plausibility check of CLTH-stuck (Digital Sensor-Bottom Clutch)
        req_data.template_name = TestCaseType.plausibility_check_of_clth_stuck_bottom.name
        doc_output_path = plausibility_check_of_clth_stuck_bottom(req_data)

    logging.info(f"报告生成结束: {doc_output_path}")
    return doc_output_path


def mst_header_page_docx(config_data: ReqPOJO, request_data: dict) -> str:
    return replace_mst_header_page_docx(config_data, request_data)
