import logging
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 定义文件夹路径
folder_path = r'C:\Users\Administrator\Downloads\output\127001\IO_Test\analogue_input\I_A_BPS\csv'

# 定义已知的前缀列表
prefixes = ['level1', 'level2', 'level3', 'level4']

# 创建一个线程池执行器，用于并行处理文件读取
executor = ThreadPoolExecutor(max_workers=4)


def read_csv(file_path):
    """读取CSV文件并返回DataFrame"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            df = pd.read_csv(f)
        return df
    except Exception as e:
        logging.error(f"Failed to read file {file_path}: {e}")
        return None


def delete_files(file_paths):
    """删除指定的文件列表"""
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f'Deleted original file: {file_path}')
            except Exception as e:
                logging.error(f"Failed to delete file {file_path}: {e}")
        else:
            logging.warning(f"File not found: {file_path}")


# 遍历每个前缀并合并对应的CSV文件
for prefix in prefixes:
    # 获取当前前缀的所有文件路径
    file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                  if f.startswith(prefix) and f.endswith('.csv')]

    # 如果没有找到对应前缀的文件，则跳过
    if not file_paths:
        logging.warning(f'No CSV files found with the prefix "{prefix}".')
        continue

    # 并行读取所有文件
    futures = [executor.submit(read_csv, file_path) for file_path in file_paths]
    df_list = [future.result() for future in futures if future.result() is not None]

    if df_list:  # 如果有文件被成功读取
        # 合并所有的DataFrame
        combined_df = pd.concat(df_list, ignore_index=True)

        # 写入新的合并后的CSV文件
        output_file_path = os.path.join(folder_path, f'{prefix}_combined.csv')
        combined_df.to_csv(output_file_path, index=False)

        logging.info(f'Successfully combined CSV files with prefix "{prefix}" into "{output_file_path}".')

        # 删除原始的CSV文件
        delete_files(file_paths)
    else:
        logging.warning(f'No files were successfully read for the prefix "{prefix}".')

# 关闭线程池执行器
executor.shutdown()
