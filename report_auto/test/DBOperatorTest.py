from asammdf import MDF

from app import connection_pool
from tools.utils.DBOperator import create_table

# 测量文件路径
measure_file_path = r'C:\Users\Administrator\Downloads\input\HTM\HTM03_idle.mf4'

# 创建 MDF 对象
mdf = MDF(measure_file_path)

# 选择需要的列
selected_columns = ['DC1_Th1', 'DC1_Th2', 'DC1_Th3', 'DC1_Th4', 'DC1_Th5', 'DC1_Th6', 'DC1_Th7',
                    'DC1_Th8', 'TC1_Th1', 'TC1_Th2', 'TC1_Th3', 'TC1_Th4', 'TC1_Th5', 'TC1_Th6',
                    'TC1_Th7', 'TC1_Th8', 'TC1_Th9', 'TC1_Th10', 'TC1_Th11', 'TC1_Th12', 'TC1_Th13',
                    'TC1_Th14', 'TC1_Th15', 'TC1_Th16', 'TC2_Th1', 'TC2_Th2', 'TC2_Th3', 'TC2_Th4',
                    'TC2_Th5', 'TC2_Th6', 'TC2_Th7', 'TC2_Th8', 'TC2_Th9', 'TC2_Th10', 'TC2_Th11',
                    'TC2_Th12', 'TC2_Th13', 'TECU_t']
# 将数据转换为 DataFrame
df = mdf.to_dataframe(channels=selected_columns)

# 去除连续的重复行
# 首先对 DataFrame 进行排序，确保按时间顺序排列
df.sort_values(by='timestamps', inplace=True)

# 使用 keep='first' 选项保留第一次出现的非重复行
unique_rows_df = df.drop_duplicates(keep='first')
unique_rows_df = unique_rows_df.reset_index()
# 使用 apply 方法对每一列应用 between 方法
unique_rows_df = unique_rows_df[unique_rows_df[selected_columns].apply(lambda x: x.between(-100, 200)).all(axis=1)]
print(unique_rows_df)

# 表名
table_name = 'chip_temperature'

# 获取连接
connection = connection_pool.get_connection()
# 创建表
create_table(connection, table_name, unique_rows_df)
# 批量插入表
# batch_insert_data(connection, table_name, unique_rows_df)
