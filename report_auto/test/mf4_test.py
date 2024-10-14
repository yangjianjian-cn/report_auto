# __coding__ = "utf-8"
# from asammdf import MDF
#
# # 假设 data 字典中包含了测量文件的路径
# data = {
#     'measure_file_path': r'C:\Users\Administrator\Downloads\GWM_POER_OBD_V200_G143_phase4.mf4'
# }
#
# # 获取测量文件的路径
# measure_file_path = data['measure_file_path']
#
# # 使用 MDF 类加载测量文件
# mdf = MDF(measure_file_path)
#
# # 将所有信号列转换为 DataFrame
# # df = mdf.to_dataframe(channels=['TECU_tRaw'])
# df = mdf.to_dataframe()
#
# # 将 DataFrame 保存到 CSV 文件
# output_file_path = r'C:\Users\Administrator\Downloads\output\all_signals.csv'
# with open(output_file_path, 'w', newline='') as f:
#     df.to_csv(f, index=True)
#
# print(f"All signals have been saved to {output_file_path}")