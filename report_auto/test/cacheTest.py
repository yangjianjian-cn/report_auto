from config.ConfigReader import ConfigReader

# 假设配置文件名为 "config.ini"
config_file_path = "../config/report_auto.ini"

reader = ConfigReader(config_file_path)

# 获取所有设置
all_settings = reader.get_all_settings()
print("All Settings:", all_settings)

# 获取特定设置
input_path = reader.get_setting('input_path')
print("Input Path:", input_path)