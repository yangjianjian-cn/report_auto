import os

import pandas as pd

# 定义文件夹路径
folder_path = r'C:\Users\Administrator\Downloads\output\127001\IO_Test\analogue_input\I_A_BPS\csv'

# 定义已知的前缀列表
prefixes = ['level1', 'level2', 'level3', 'level4']

# 遍历每个前缀并合并对应的CSV文件
for prefix in prefixes:
    # 获取当前前缀的所有文件路径
    file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                  if f.lower().startswith(prefix) and f.endswith('.csv')]

    # 如果没有找到对应前缀的文件，则跳过
    if not file_paths:
        print(f'No CSV files found with the prefix "{prefix}".')
        continue

    # 读取所有文件并存储在列表中
    df_list = []
    for file_path in file_paths:
        try:
            df = pd.read_csv(file_path)
            df_list.append(df)
        except Exception as e:
            print(f"Failed to read file {file_path}: {e}")

    if df_list:  # 如果有文件被成功读取
        # 合并所有的DataFrame
        combined_df = pd.concat(df_list, ignore_index=True)

        # 写入新的合并后的CSV文件
        output_file_path = os.path.join(folder_path, f'{prefix}.csv')
        combined_df.to_csv(output_file_path, index=False)

        print(f'Successfully combined CSV files with prefix "{prefix}" into "{output_file_path}".')

        # 删除原始的CSV文件
        for file_path in file_paths:
            try:
                os.remove(file_path)
                print(f'Deleted original file: {file_path}')
            except Exception as e:
                print(f"Failed to delete file {file_path}: {e}")
    else:
        print(f'No files were successfully read for the prefix "{prefix}".')
