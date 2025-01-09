import glob
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd


# CSV文件合并器
class CSVCombiner:
    def __init__(self, folder_path:str, prefixes:str):
        self.folder_path = folder_path
        self.prefixes = prefixes
        # 配置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def read_csv(self, file_path):
        """读取CSV文件并返回DataFrame"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            return df
        except Exception as e:
            logging.error(f"Failed to read file {file_path}: {e}")
            return None

    def delete_files(self, file_paths):
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

    def combine_csvs(self):
        """遍历每个前缀并合并对应的CSV文件"""
        for prefix in self.prefixes:
            # 获取当前前缀的所有文件路径
            pattern = os.path.join(self.folder_path, f'{prefix}*.csv')
            file_paths = glob.glob(pattern)

            # 如果没有找到对应前缀的文件，则跳过
            if not file_paths:
                logging.warning(f'No CSV files found with the prefix "{prefix}".')
                continue

            # 并行读取所有文件
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(self.read_csv, file_path) for file_path in file_paths]
                df_list = [future.result() for future in futures if future.result() is not None]

            if df_list:  # 如果有文件被成功读取
                # 合并所有的DataFrame
                combined_df = pd.concat(df_list, ignore_index=True)

                # 写入新的合并后的CSV文件
                output_file_path = os.path.join(self.folder_path, f'{prefix}.csv')
                combined_df.to_csv(output_file_path, index=False)

                logging.info(f'Successfully combined CSV files with prefix "{prefix}" into "{output_file_path}".')

                # 等待一段时间再删除原始文件
                delay = 2 # 休眠10秒
                logging.info(f'Waiting for {delay} seconds before deleting original files...')
                time.sleep(delay)

                # 删除原始的CSV文件
                self.delete_files(file_paths)
            else:
                logging.warning(f'No files were successfully read for the prefix "{prefix}".')
