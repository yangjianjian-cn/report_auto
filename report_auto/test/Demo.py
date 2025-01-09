import os
import shutil

# 定义源文件路径和目标文件路径
source_file = r'C:\Users\Administrator\Downloads\template\IOTest_Main_Tmplt.xlsm'
destination_dir = r'C:\Users\Administrator\Downloads\output\127001\xlsm'
destination_file = os.path.join(destination_dir, 'IOTest_Main_Tmplt.xlsm')

# 确保目标目录存在，如果不存在则创建它
os.makedirs(destination_dir, exist_ok=True)

try:
    # 复制文件到目标位置
    shutil.copy2(source_file, destination_file)
    print(f"文件已成功复制到 {destination_file}")
except IOError as e:
    print(f"无法复制文件. I/O错误: {e}")
except Exception as e:
    print(f"复制文件时发生错误: {e}")
