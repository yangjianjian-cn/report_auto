__coding__ = "utf-8"

# from asammdf import MDF
#
# filepath = 'file/HTM03_idle.mf4'
# mdf = MDF(filepath)
# df = mdf.to_dataframe()
#
# csv_file = 'file/HTM03_idle.csv'
# with open(csv_file, 'w', newline='') as f:
#     df.to_csv(f, index=True)

selected_columns_dc1 = ['DC1_Th1', 'DC1_Th2', 'DC1_Th3', 'DC1_Th4', 'DC1_Th5', 'DC1_Th6', 'DC1_Th7', 'DC1_Th8',
                        'TECU_t', 'timestamps']
# 移除最后一个元素
selected_columns_dc1.pop()

# 输出修改后的列表
print(selected_columns_dc1)