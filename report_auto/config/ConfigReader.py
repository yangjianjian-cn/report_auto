import configparser


class ConfigReader:
    _instance = None  # 单例模式的实例存储
    _cache = {}  # 缓存配置项

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigReader, cls).__new__(cls)
            cls._instance.config = configparser.ConfigParser()
            cls._instance.config.read(kwargs.get('config_file_path', 'config.ini'))
        return cls._instance

    def get_setting(self, option):
        """Get the value for a given setting from cache or configuration file."""
        if option not in self._cache:
            if self.config.has_option('settings', option):
                self._cache[option] = self.config.get('settings', option)
            else:
                raise ValueError(f"Option '{option}' not found in the 'settings' section.")
        return self._cache[option]

    def get_all_settings(self):
        """Get all settings as a dictionary. Read from cache if available."""
        if not self._cache:
            if self.config.has_section('settings'):
                self._cache.update(dict(self.config.items('settings')))
            else:
                raise ValueError("Section 'settings' not found in the configuration file.")
        return self._cache

# 使用示例
# if __name__ == "__main__":
#     # 创建 ConfigReader 实例
#     config_reader = ConfigReader(config_file_path="path/to/your/config.ini")
#
#     # 获取所有设置
#     all_settings = config_reader.get_all_settings()
#     print("All Settings:", all_settings)
#
#     # 获取特定设置
#     input_path = config_reader.get_setting('input_path')
#     print("Input Path:", input_path)
