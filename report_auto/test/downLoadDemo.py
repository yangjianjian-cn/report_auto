import requests

# 目标URL
url = 'https://cdn.jsdelivr.net/npm/jquery@3.3.1/dist/jquery.min.js'

# 请求文件
response = requests.get(url)

# 检查请求是否成功
if response.status_code == 200:
    # 指定要保存文件的路径
    file_path = '../static/js/jquery.min.js'

    # 将文件内容写入本地文件
    with open(file_path, 'wb') as f:
        f.write(response.content)

    print(f"文件已成功下载到 {file_path}")
else:
    print(f"无法下载文件，状态码: {response.status_code}")
