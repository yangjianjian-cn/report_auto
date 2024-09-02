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
from tools.conversion.redundant_brake_plausibility_check_parser import redundant_brake_plausibility_check

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

'''csvPath: str, outputPath: str'''


def mst_report(req_data: ReqPOJO) -> str:
    logging.info(f'开始生成:{req_data.csv_path}')
    csv_file_name: str = os.path.basename(req_data.csv_path)
    logging.info(f"文件名:{csv_file_name}")

    if TestCaseType.brake_override_accelerator.value in csv_file_name.lower():
        # 1.Brake_Override_Accelerator
        req_data.template_name = TestCaseType.brake_override_accelerator.name
        doc_output_path = brake_override_accelerator(req_data)
        logging.info(f"已生成: {doc_output_path}")

    elif TestCaseType.main_brake_plausibility_check.value in csv_file_name.lower():
        # 2Main Brake Plausibility Check (DIO)
        req_data.template_name = TestCaseType.main_brake_plausibility_check.name
        doc_output_path = main_brake_plausibility_check(req_data)
        logging.info(f"已生成: {doc_output_path}")

    elif TestCaseType.redundant_brake_plausibility_check.value in csv_file_name.lower():
        # 3Redundant Brake Plausibility Check (DIO)
        doc_output_path = redundant_brake_plausibility_check(req_data)
        logging.info(f"已生成: {doc_output_path}")
    return doc_output_path
