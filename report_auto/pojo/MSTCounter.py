import json


class MSTCounter:
    def __init__(self, mst_test=0, app_pl_br_1=0, brk_04=0, brk_05=0, ngs_06=0, clth_05=0, clth_06=0):
        self.mst_test = mst_test
        self.app_pl_br_1 = app_pl_br_1
        self.brk_04 = brk_04
        self.brk_05 = brk_05
        self.ngs_06 = ngs_06
        self.clth_05 = clth_05
        self.clth_06 = clth_06

    def update_attribute(self, attribute_name):
        if hasattr(self, attribute_name):
            setattr(self, attribute_name, getattr(self, attribute_name) + 1)
        else:
            raise AttributeError(f"No such attribute: {attribute_name}")


def load_from_mst_json(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            if content == '':
                return MSTCounter()  # 文件为空，返回默认对象
            else:
                data = json.loads(content)
                return MSTCounter(**data)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None


def save_to_mst_json(file_path, obj):
    try:
        with open(file_path, 'w') as file:
            json.dump(obj.__dict__, file, indent=4)
    except Exception as e:
        print(f"Failed to save to JSON: {e}")


if __name__ == "__main__":
    file_path = 'mstcounter1.json'  # JSON 文件路径

    # 读取 JSON 文件并转换为 MSTCounter 对象
    counter = load_from_mst_json(file_path)

    # 如果文件内容为空或无法解析，创建默认对象
    if counter is None:
        counter = MSTCounter()

    # 更新属性值
    test_scenario = 'app_pl_br_1'  # 示例：更新 app_pl_br_1 的值
    counter.update_attribute(test_scenario)

    # 打印更新后的属性值
    print(f"Updated app_pl_br_1 value after increment: {counter.app_pl_br_1}")

    # 保存更新后的对象到 JSON 文件
    save_to_mst_json(file_path, counter)
