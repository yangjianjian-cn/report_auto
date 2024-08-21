
import os
import zipfile

# 已有的输出路径
outputPath = 'C:\\Users\\Administrator\\Downloads\\RE__ECU_MST_Auto-test_report_follow_up\\MST_L1\\output'

# 添加 "docx" 子目录
outputPath = os.path.join(outputPath, 'docx')

# 确保目录存在
if not os.path.exists(outputPath):
    print(f"Directory {outputPath} does not exist.")
else:
    # 创建一个 ZIP 文件
    zip_filename = 'output_files.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历目录及其子目录
        for root, dirs, files in os.walk(outputPath):
            for file in files:
                # 构建完整的文件路径
                file_path = os.path.join(root, file)
                # 在 ZIP 文件中存储文件
                zipf.write(file_path, os.path.relpath(file_path, outputPath))

    print(f"All files in {outputPath} have been zipped into {zip_filename}.")