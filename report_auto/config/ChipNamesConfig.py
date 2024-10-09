import configparser
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ChipNamesConfig:
    _instance = None

    def __new__(cls, config_path: str = 'chip_names.ini') -> 'ChipNamesConfig':
        if not cls._instance:
            cls._instance = super().__new__(cls)
            try:
                cls._instance.config = cls.load_config(config_path)
                cls._instance.config_dict = cls._load_into_memory(cls._instance.config)
                logging.info("chip_names.ini Configuration loaded successfully into memory.")
                logging.debug(f"Loaded configuration: {cls._instance.config_dict}")
            except Exception as e:
                logging.error(f"Failed to load configuration: {e}")
                raise
        return cls._instance

    @staticmethod
    def load_config(config_path: str) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.optionxform = str  # 禁用将选项名称转换为小写
        try:
            with open(config_path, encoding='utf8') as fp:
                config.read_file(fp)
        except UnicodeDecodeError as e:
            logging.error(f"Unicode decode error: {e}")
            raise
        except FileNotFoundError as e:
            logging.error(f"File not found: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise
        return config

    @staticmethod
    def _load_into_memory(config: configparser.ConfigParser) -> dict:
        config_dict = {}
        for section in config.sections():
            config_dict[section] = {}
            for key, value in config.items(section):
                key_stripped = key.strip()
                value_stripped = value.strip()
                config_dict[section][key_stripped] = value_stripped
                logging.debug(f"Loaded key-value pair: [{section}] {key_stripped} = {value_stripped}")
        return config_dict

    def get(self, section: str, key: str) -> str:
        try:
            return self.config_dict[section][key.strip()]
        except KeyError as e:
            logging.error(f"Key not found: [{section}] {key}")
            return key.strip()

    def get_int(self, section: str, key: str) -> int:
        try:
            return int(self.config_dict[section][key.strip()])
        except KeyError as e:
            logging.error(f"Key not found: [{section}] {key}")
            raise
        except ValueError as e:
            logging.error(f"Value error for key [{section}] {key}: {e}")
            raise

    def get_float(self, section: str, key: str) -> float:
        try:
            return float(self.config_dict[section][key.strip()])
        except KeyError as e:
            logging.error(f"Key not found: [{section}] {key}")
            raise
        except ValueError as e:
            logging.error(f"Value error for key [{section}] {key}: {e}")
            raise

    def get_boolean(self, section: str, key: str) -> bool:
        try:
            value = self.config_dict[section][key.strip()].lower()
            if value == 'true':
                return True
            elif value == 'false':
                return False
            else:
                raise ValueError(f"Invalid boolean value: {value}")
        except KeyError as e:
            logging.error(f"Key not found: [{section}] {key}")
            raise
        except ValueError as e:
            logging.error(f"Value error for key [{section}] {key}: {e}")
            raise


# 示例用法
# if __name__ == "__main__":
#     config = ChipNamesConfig()
#
#     # 获取配置项
#     try:
#         dc1_th1 = config.get('chip_names', 'DC1_Th1')
#         tc1_th1 = config.get('chip_names', 'TC1_Th1')
#         tc2_th1 = config.get('chip_names', 'TC2_Th1')
#         tc2_th10 = config.get('chip_names', 'TC2_Th10')
#
#         print(f"DC1_Th1: {dc1_th1}")
#         print(f"TC1_Th1: {tc1_th1}")
#         print(f"TC2_Th1: {tc2_th1}")
#         print(f"TC2_Th10: {tc2_th10}")
#     except KeyError as e:
#         logging.error(f"Key not found: {e}")
