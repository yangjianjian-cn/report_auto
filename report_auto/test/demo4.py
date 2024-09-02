import os

csv_path = r'C:\Users\Administrator\Downloads\output\MST_Test\template\brake_override_accelerator.docx'

# 提取最后一级目录
last_dir = os.path.basename(csv_path)

# 提取次一级目录
second_last_dir = os.path.basename(os.path.dirname(csv_path))

# 提取次三级目录
third_last_dir = os.path.basename(os.path.dirname(os.path.dirname(csv_path)))

print("Last directory:", last_dir)
print("Second last directory:", second_last_dir)
print("Third last directory:", third_last_dir)

parent_dir = os.path.dirname(csv_path)
print(f'parent_dir:{parent_dir}')
