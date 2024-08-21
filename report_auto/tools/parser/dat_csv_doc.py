import os
import logging
import zipfile

from constant.TestCaseType import TestCaseType
from tools.common.dat_csv_common import dat_csv_conversion
from tools.conversion.brake_override_accelerator_parser import brake_override_accelerator
from tools.conversion.main_brake_plausibility_check_parser import main_brake_plausibility_check
from tools.conversion.redundant_brake_plausibility_check_parser import redundant_brake_plausibility_check

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def docx_zip(docxPath, zipPath) -> str:
    logging.info(f"docxPath:{docxPath}")
    logging.info(f"zipPath:{zipPath}")

    # 构建完整的 ZIP 文件路径
    zip_file_name = 'output_files.zip'
    zip_file_path = os.path.join(zipPath, zip_file_name)

    # 创建 ZIP 文件
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历目录及其子目录
        for root, dirs, files in os.walk(docxPath):
            for file in files:
                # 构建完整的文件路径
                file_path = os.path.join(root, file)
                # 在 ZIP 文件中存储文件
                zipf.write(file_path, os.path.relpath(file_path, docxPath))
    logging.info(f"zip_file_path:{zip_file_path}")
    return zip_file_name, zip_file_path


def dat_csv_docx(datPath: str, outputPath: str):
    csvPathList = []
    logging.info("\r\n开始转换...")
    dat_files = [f for f in os.listdir(datPath) if f.endswith('.dat')]
    for dat_file in dat_files:
        errMsg = dat_csv_conversion(dat_file, datPath, outputPath)
        if errMsg.startswith("err:"):
            logging.error(f'文件{dat_file}解析异常:{errMsg}')
        else:
            csvPathList.append(errMsg)
            logging.info(f"转换完成:{errMsg}")

    logging.info(f"\r\n{dat_file} 报告生成中...")
    if csvPathList:
        # 如果csvPathList不为空，则遍历它
        for csvPath in csvPathList:
            logging.info(f'开始生成:{csvPath}')
            csv_file_name: str = os.path.basename(csvPath)

            if TestCaseType.brake_override_accelerator.value in csv_file_name.lower():
                # 1.Brake_Override_Accelerator
                doc_output_path = brake_override_accelerator(csvPath, TestCaseType.brake_override_accelerator.name)
                logging.info(f"已生成: {doc_output_path}\r\n")

            elif TestCaseType.main_brake_plausibility_check.value in csv_file_name.lower():
                # 2Main Brake Plausibility Check (DIO)
                doc_output_path = main_brake_plausibility_check(csvPath,
                                                                TestCaseType.main_brake_plausibility_check.name)
                logging.info(f"已生成: {doc_output_path}\r\n")

            elif TestCaseType.redundant_brake_plausibility_check.value in csv_file_name.lower():
                # 3Redundant Brake Plausibility Check (DIO)
                doc_output_path = redundant_brake_plausibility_check(csvPath,
                                                                     TestCaseType.redundant_brake_plausibility_check.name)
                logging.info(f"已生成: {doc_output_path}\r\n")
