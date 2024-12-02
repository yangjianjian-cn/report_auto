__coding__ = "utf-8"

import logging
import os

from asammdf import MDF
from flask import request

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# 获取客户端IP地址
def getClientIp():
    if 'X-Forwarded-For' in request.headers:
        x_forwarded_for = request.headers['X-Forwarded-For']
        # 分割并获取最后一个IP地址
        client_ips = x_forwarded_for.split(',')
        client_ip = client_ips[-1].strip()
    else:
        # 如果没有 X-Forwarded-For 头部，则直接使用远程地址
        client_ip = request.remote_addr
    client_ip = client_ip.replace('.', '')
    logging.info(f"client_ip:{client_ip}")
    return client_ip


def merge(file_name, total_chunks, save_path) -> str:
    save_file = os.path.join(save_path, file_name)

    # 检查所有分片文件是否存在
    temp_files = [os.path.join(save_path, f'{file_name}.part{i}') for i in range(total_chunks)]
    for temp_file in temp_files:
        if not os.path.exists(temp_file):
            raise FileNotFoundError(f'Missing chunk file: {temp_file}')

    # 合并文件
    with open(save_file, 'wb') as outfile:
        for temp_file in temp_files:
            with open(temp_file, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(temp_file)

    return save_file


# 测量文件数据入库
def sort_and_convert(data):
    """排序并转换数据结构，添加索引"""
    sorted_data = dict(sorted(data.items(), key=lambda item: float(item[0].split(' ~ ')[0])))
    return [
        {**{key: value}, 'idx': idx}
        for idx, (key, value) in enumerate(sorted_data.items())
    ]


# ECU-HTM,获取信号列列名称，（配置允许的文件扩展名）
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
