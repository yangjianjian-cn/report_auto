# 使用精简版的Python 3.9镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装依赖
COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# 复制应用代码到镜像中
COPY . .

# 设置环境变量
ENV FLASK_ENV=production
ENV FLASK_APP=main.py

# 使用Gunicorn来启动Flask应用
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "main:main", "--timeout", "300"]