import os
from pathlib import Path

filtered_set = {}
element_count = len(filtered_set)
print(element_count)

# C:\Users\Administrator\Downloads\RE__ECU_MST_Auto - test_report_follow_up\MST_L1\output\IOTest\csv\Level1.csv
# 输出目录
csvPath = "C:\\Users\\Administrator\\Downloads\\RE__ECU_MST_Auto-test_report_follow_up\\MST_L1\\output\\IOTest\\csv"
directory_before_csv = os.path.dirname()
directory_output = os.path.dirname(directory_before_csv)
# 输出文件名
output_name = Path(csvPath).stem
