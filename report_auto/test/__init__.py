import pandas as pd
from asammdf import MDF

measure_file_path = r'C:\Users\Administrator\Downloads\input\HTM\127001\highway.dat'
mdf = MDF(measure_file_path)

# 获取所有信号（列）的信息
columns_info = mdf.channels_db
column_names = list(columns_info.keys())
print(column_names)

# signal_names = ['TC1_Th9', 'TC1_Th9_ECU25']
# signals = mdf.select(signal_names)
# df = pd.DataFrame()
# for signal in signals:
#     df[signal.name] = signal.samples[:20]  # 只取前20行
