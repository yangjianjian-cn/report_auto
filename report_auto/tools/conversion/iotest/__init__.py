__coding__ = "utf-8"

from pathlib import Path

# 指定要遍历的目录路径
csv_path = Path(r'C:\Users\Administrator\Downloads\output\127001\IO_Test\analogue_input\I_A_APP1\csv')

# 遍历目录
for file_path in csv_path.glob('**/*'):
    if file_path.is_file():
        # 打印每个文件的完整路径
        # print(file_path)
        pass
