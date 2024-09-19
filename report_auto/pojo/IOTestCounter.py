import json


class IOTestCounter:
    def __init__(self, io_test=0, analogue_input=0, digital_input=0, pwm_input=0, digital_output=0, pwm_output=0):
        self.io_test = io_test
        self.analogue_input = analogue_input
        self.digital_input = digital_input
        self.pwm_input = pwm_input
        self.digital_output = digital_output
        self.pwm_output = pwm_output

    def update_attribute(self, attribute_name):
        if hasattr(self, attribute_name):
            setattr(self, attribute_name, getattr(self, attribute_name) + 1)
        else:
            raise AttributeError(f"No such attribute: {attribute_name}")


def load_from_io_json(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            if content == '':
                return IOTestCounter()  # 文件为空，返回默认对象
            else:
                data = json.loads(content)
                return IOTestCounter(**data)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None


def save_to_io_json(file_path, obj):
    try:
        with open(file_path, 'w') as file:
            json.dump(obj.__dict__, file, indent=4)
    except Exception as e:
        print(f"Failed to save to JSON: {e}")


# if __name__ == "__main__":
#     file_path = r'..\io_report_counter.json'  # JSON 文件路径
#
#     # 读取 JSON 文件并转换为 IOTestCounter 对象
#     counter = load_from_io_json(file_path)
#
#     # 如果文件内容为空或无法解析，创建默认对象
#     if counter is None:
#         counter = IOTestCounter()
#
#     # 更新属性值
#     test_scenario = 'analogue_input'
#     counter.update_attribute(test_scenario)
#
#     # 打印更新后的属性值
#     print(f"Updated Analogue Input value after increment: {counter.analogue_input}")
#
#     # 保存更新后的对象到 JSON 文件
#     save_to_io_json(file_path, counter)
