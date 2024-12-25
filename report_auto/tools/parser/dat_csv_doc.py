import logging
import os
from pathlib import Path

from pojo.IOTestCounter import load_from_io_json, IOTestCounter, save_to_io_json
from pojo.MSTCounter import load_from_mst_json, MSTCounter, save_to_mst_json
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.dat_csv_common import dat_csv_conversion
from tools.conversion.iotest.analysis_dat import dat_data_analysis
from tools.conversion.msttest.mst_report_generation import mst_report, mst_header_page_docx
from tools.report.report_generation import replace_blank
from tools.utils.CustomException import CustomException
from tools.utils.FileUtils import get_filename_without_extension, merge_docs

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def docx_merge(output_path: str, merge_path: str, file_name: str, clientIp: str):
    # 构建完整的 ZIP 文件路径
    merge_file_name = 'RBCD_L1_ECUMST_Test_Case_V03.docx'
    merge_docx_path = os.path.join(merge_path, merge_file_name)

    docx_file_paths = []
    header_file_path: str = os.path.join(output_path, 'mst_header.docx')
    if os.path.exists(header_file_path):
        # 报告生成结果
        replace_blank(header_file_path, clientIp, file_name)
        docx_file_paths.append(header_file_path)

    # 遍历目录及其子目录
    for root, dirs, files in os.walk(output_path):
        for file in files:
            basename = os.path.basename(file)  # 获取文件的基本名称
            filename_without_extension, _ = os.path.splitext(basename)

            if filename_without_extension in file_name:
                # 构建完整的文件路径
                file_path = os.path.join(root, file)
                docx_file_paths.append(file_path)

    merge_docs(merge_docx_path, docx_file_paths)

    return merge_file_name, merge_docx_path


def join_with_br(messages):
    return ('<br>'.join(messages) + '<br>') if messages else ''


def dat_csv_docx(req_data: ReqPOJO):
    csvPathList = []  # 存储 转换成功的CSV文件路径
    u_files: str = req_data.u_files

    # 1.测量数据转换成csv文件
    # all_files = os.listdir(req_data.dat_path)
    all_files = list(Path(req_data.dat_path).glob('*.dat'))
    for file in all_files:
        if file.name not in u_files:
            continue
        # dat文件转csv
        receive_msg = dat_csv_conversion(file.name, req_data)
        if receive_msg.startswith("err:"):
            # 转换异常
            logging.error(f'文件{file}解析异常:{receive_msg}')
        else:
            # 成功转换csv
            csvPathList.append(receive_msg)
            logging.info(f"转换完成:{receive_msg}")

    # 2.MST生成报告
    success_messages = []
    error_messages = []
    if 'MST_Test' == req_data.test_team:
        for csvPath in csvPathList:
            fname_no_extension = get_filename_without_extension(csvPath)
            if fname_no_extension in u_files:
                req_data.csv_path = csvPath
                try:
                    # 生成测试报告
                    msg = mst_report(req_data)
                    contains_succeed = any('succeed' in m for m in msg)
                    file_name = get_filename_without_extension(req_data.csv_path)

                    if contains_succeed:
                        success_msg_list = [m.replace('succeed:', '') for m in msg]
                        success_msg_str = ''.join(success_msg_list)
                        success_messages.append(file_name + ' report generated successfully ' + success_msg_str)
                        updateCounter(req_data)
                    else:
                        error_msg_str = ''.join(msg)
                        error_messages.append(file_name + ' report generated unsuccessfully ' + error_msg_str)
                except Exception as e:
                    raise CustomException(f"report generation exception:{e}")

        html_success = join_with_br(success_messages)
        html_error = join_with_br(error_messages)
        return html_success, html_error

    # 3.IOTest生成报告
    else:
        try:
            return_msg_str = dat_data_analysis(req_data)
            updateCounter(req_data)
            success_messages.clear()
            if not return_msg_str:
                success_messages.append('Successfully: %s, %s' % (req_data.test_area, req_data.test_area_dataLabel))
            else:
                success_messages.append(
                    'UnSuccessfully: %s, %s,%s' % (req_data.test_area, req_data.test_area_dataLabel, return_msg_str))
        except Exception as e:
            error_messages.clear()
            success_messages.append(
                'UnSuccessfully: {}, {}, {}'.format(req_data.test_area, req_data.test_area_dataLabel, str(e)))
            logging.error(f"report generation exception:{str(e)}")

        html_success = join_with_br(success_messages)
        html_error = join_with_br(error_messages)
        return html_success, html_error

    return success_messages, error_messages


"""
统计报告数量
"""


def updateCounter(req_data: ReqPOJO):
    test_team: str = req_data.test_team
    test_team_lower = test_team.lower()

    template_path = req_data.template_path
    counter_path = os.path.join(template_path, 'counter')

    if 'MST_Test' == test_team:
        counter_mst_file = os.path.join(counter_path, 'mst_report_counter.json')
        mst_counter = load_from_mst_json(counter_mst_file)

        # 如果文件内容为空或无法解析，创建默认对象
        if mst_counter is None:
            mst_counter = MSTCounter()
        mst_counter.update_attribute(test_team_lower)

        file_name: str = get_filename_without_extension(req_data.csv_path)
        test_scenario = file_name.lower()
        mst_counter.update_attribute(test_scenario)

        save_to_mst_json(counter_mst_file, mst_counter)

    elif 'IO_Test' == test_team:
        counter_io_file = os.path.join(counter_path, 'io_report_counter.json')
        io_counter = load_from_io_json(counter_io_file)

        # 如果文件内容为空或无法解析，创建默认对象
        if io_counter is None:
            io_counter = IOTestCounter()
        io_counter.update_attribute(test_team_lower)

        file_name: str = req_data.test_scenario
        test_scenario = file_name.lower()
        io_counter.update_attribute(test_scenario)

        save_to_io_json(counter_io_file, io_counter)


"""
MST测试报告首页
"""


def mst_header_page(config_data: ReqPOJO, request_data: dict) -> str:
    return mst_header_page_docx(config_data, request_data)
