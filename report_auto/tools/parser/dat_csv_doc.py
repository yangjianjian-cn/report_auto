import logging
import os
import zipfile

from constant.TestCaseType import fuzzy_match_test_case_type, TestCaseType
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.dat_csv_common import dat_csv_conversion
from tools.conversion.iotest.analogue_input_parser import analogue_input
from tools.conversion.msttest.mst_report_generation import mst_report
from tools.utils.CustomException import CustomException
from tools.utils.RedisUtils import RedisCounter, getRedisConnector

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def docx_zip(outputPath: str, zipPath: str, fileName: str) -> str:
    # 构建完整的 ZIP 文件路径
    zip_file_name = 'output_files.zip'
    zip_file_path = os.path.join(zipPath, zip_file_name)

    # 创建 ZIP 文件
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历目录及其子目录
        for root, dirs, files in os.walk(outputPath):
            for file in files:
                basename = os.path.basename(file)  # 获取文件的基本名称
                filename_without_extension, _ = os.path.splitext(basename)
                logging.info(f"base_name:{filename_without_extension}")

                if filename_without_extension in fileName:
                    # 构建完整的文件路径
                    file_path = os.path.join(root, file)
                    # 在 ZIP 文件中存储文件
                    zipf.write(file_path, os.path.relpath(file_path, outputPath))
    logging.info(f"zip_file_path:{zip_file_path}")
    return zip_file_name, zip_file_path


'''
datPath: dat文件目录 ，测试团队/测试区域/测试功能
outputPath: 输出目录, 测试团队/测试区域
test_type: 测试场景,I/O Test, MST Test
test_area: 测试区域
datPath: str, outputPath: str, test_team: str, test_scenario: str, test_area: str
'''


def dat_csv_docx(req_data: ReqPOJO) -> str:
    csvPathList = []
    # 1.dat转换成csv
    dat_files = [f for f in os.listdir(req_data.dat_path) if f.endswith('.dat')]
    for dat_file in dat_files:
        errMsg = dat_csv_conversion(dat_file, req_data)
        if errMsg.startswith("err:"):
            logging.error(f'文件{dat_file}解析异常:{errMsg}')
        else:
            csvPathList.append(errMsg)
            logging.info(f"转换完成:{errMsg}")

    # 2.生成报告
    ret_output_path = []
    if csvPathList and 'MST_Test' == req_data.test_team:
        for csvPath in csvPathList:
            req_data.csv_path = csvPath
            try:
                output_path = mst_report(req_data)
                ret_output_path.append(output_path)
                ret_output_path.append("<br/>")
                updateRedisCounter(req_data)
            except Exception as e:
                raise CustomException(f"report generation exception:{e}")
        return ret_output_path

    # 3.IOTest 生成测试报告
    if csvPathList and req_data.test_team == 'IO_Test' and req_data.test_scenario == 'AnalogueInput' and req_data.test_area == 'I_A_APP1':
        try:
            output_path = analogue_input(req_data)
            ret_output_path.append(output_path)
            ret_output_path.append("<br/>")
            updateRedisCounter(req_data)
        except Exception as e:
            raise CustomException(f"report generation exception:{e}")
    return ret_output_path


'''连接Redis,更新Key对应数量'''


def updateRedisCounter(req_data: ReqPOJO):
    # 'IP:PORT:PASSWD:DB'
    redis_connector: str = req_data.redis_connector
    redis_counter: RedisCounter = getRedisConnector(redis_connector)
    redis_counter.key_name = req_data.test_team
    redis_counter.increment()  # 测试项目数量加1

    if req_data.test_scenario:
        redis_counter.key_name = req_data.test_scenario
        redis_counter.increment()  # IOTest测试场景数量加1

    if 'MST_Test' == req_data.test_team:
        # 根据文件名称，求统计量
        csv_file_name_with_ext: str = os.path.basename(req_data.csv_path)
        csv_file_name_without_ext, _ = os.path.splitext(csv_file_name_with_ext)
        csv_file_name_without_ext: str = csv_file_name_without_ext.lower()
        matched_cases: TestCaseType = fuzzy_match_test_case_type(csv_file_name_without_ext)
        if matched_cases is not None:
            redis_counter.key_name = matched_cases.value
            redis_counter.increment()  # MSTTest测试场景数量加1
