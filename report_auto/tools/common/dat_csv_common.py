import logging
import os
from pathlib import Path

from asammdf import MDF

from pojo.IOTestCounter import load_from_io_json, IOTestCounter
from pojo.MSTCounter import load_from_mst_json, MSTCounter
from pojo.MSTReqPOJO import ReqPOJO
from tools.common.csv_column_rename import reMstDF
from tools.conversion.iotest.analysis_todb import IOTestDataInDB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def create_file_path(dat_file: str, output_file_name_ext: str, output_path: str, sub_dir: str):
    # 提取文件名（不包括扩展名）
    output_file_name = Path(dat_file).stem
    # 构建文件名
    target_file = f"{output_file_name}.{output_file_name_ext}"
    # 构建输出路径
    output_file_path = Path(output_path) / sub_dir / target_file
    logging.debug(f"output_file_name={output_file_name}")
    logging.debug(f"target_file={target_file}")
    logging.debug(f"output_file_path={output_file_path}")

    # 创建必要的目录
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    return target_file, str(output_file_path)


"""
文件转换 dat -> csv
dat_file: dat文件名称
inputPath: dat文件所在目录， 测试团队/测试区域/测试功能
outputPath: csv文件输出目录， 测试团队/测试区域
inputPath: str, outputPath: str,test_team: str,test_type: str,test_area: str
"""


def dat_csv_conversion(dat_file: str, req_data: ReqPOJO) -> str:
    filepath = os.path.join(req_data.dat_path, dat_file)
    try:
        # 测试项目/测试区域/测试功能
        output_file_name, csv_file = create_file_path(dat_file, "csv", req_data.csv_path, "csv")

        # MDF数据转换为DataFrame
        if 'MST_Test' == req_data.test_team:
            # MST测量数据
            mdf = MDF(filepath)
            df = mdf.to_dataframe()

            column_names = df.columns.tolist()
            alias_column_names = {item: item.split('\\')[0] for item in column_names}
            df.rename(columns=alias_column_names, inplace=True)

            df = reMstDF(df, output_file_name)
            with open(csv_file, 'w', newline='') as f:
                df.to_csv(f, index=True)

        elif 'IO_Test' == req_data.test_team:
            # IO Test测量数据
            mdf = MDF(filepath)
            df = mdf.to_dataframe()

            alias_column_names = {item: item.split('\\')[0] for item in df.columns.tolist()}
            df.rename(columns=alias_column_names, inplace=True)

            ioTestDataInDB = IOTestDataInDB()
            result_dicts: dict = ioTestDataInDB.get_io_test_data(test_area=req_data.test_area,test_scenario=req_data.test_scenario,test_area_dataLabel=req_data.test_area_dataLabel)
            db_columns_list:list = ioTestDataInDB.csv_needed_columns(result_dicts)
            logging.info(f"columns_to_include_list:{db_columns_list}")

            file_column_list:list = df.columns.tolist()
            logging.info(f"file_column_list:{file_column_list}")

            # 将 db_columns_list 转换为小写并存储在一个集合中
            db_columns_lower = {col.lower() for col in db_columns_list}
            # 保留 file_column_list 中在 db_columns_list 中存在的元素，并保持原始顺序
            columns_list = [col for col in file_column_list if col.lower() in db_columns_lower]
            logging.info(f"columns_list:{columns_list}")

            df = df[columns_list]

            with open(csv_file, 'w', newline='') as f:
                df.to_csv(f, index=True)

        elif "HTM" == req_data.test_team:
            pass

        return csv_file
    except FileNotFoundError:
        return f"err:File not found: {filepath}"
    except ValueError as ve:
        logging.error(ve)
        return f"err:Value error during conversion: {str(ve)}"
    except Exception as e:
        logging.error(e)
        return f"err:Error reading {filepath}: {str(e)}"


"""
MST和IO测试报告统计器
"""


def counter_report(template_path: str):
    counter_path = os.path.join(template_path, 'counter')
    if not os.path.exists(counter_path):
        os.makedirs(counter_path)

    # mst报告统计器
    mst_file_path = os.path.join(counter_path, 'mst_report_counter.json')
    if not os.path.exists(mst_file_path):
        mst_counter = MSTCounter()
        mst_dict = mst_counter.__dict__
    else:
        mst_counter = load_from_mst_json(mst_file_path)
        mst_dict = mst_counter.__dict__

    # io报告统计器
    io_file_path = os.path.join(counter_path, 'io_report_counter.json')
    if not os.path.exists(io_file_path):
        io_counter = IOTestCounter()
        io_dict = io_counter.__dict__
    else:
        io_counter = load_from_io_json(io_file_path)
        io_dict = io_counter.__dict__

    merged_dict = {**mst_dict, **io_dict}
    return merged_dict
