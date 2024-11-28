from asammdf import MDF


def allowed_file(filename):
    # 定义允许的文件扩展名
    ALLOWED_EXTENSIONS = {'dat', 'mf4'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_columns_from_mdf(file_path):
    # 使用 asammdf 库读取 MDF 文件并提取列名称
    mdf = MDF(file_path)
    # 定义要保留的前缀
    prefixes = ['TC1_', 'TC2_', 'DC1_', 'DC2_']
    # 提取并过滤列名称,列表中的元素类似TC1_Th16_Relay_side\ES620 _614
    columns = [
        signal.name.split('\\')[0]
        for group in mdf.groups
        for signal in group.channels
        if any(signal.name.startswith(prefix) for prefix in prefixes)
    ]
    return columns
