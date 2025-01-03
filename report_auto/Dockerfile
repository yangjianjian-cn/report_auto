# 使用Anaconda镜像
FROM continuumio/miniconda3

# 设置工作目录
WORKDIR /app

# 将当前目录的内容复制到容器的/app目录中
COPY . .

# 创建并激活新的Conda环境
RUN conda env create -f environment.yml
SHELL ["conda", "run", "-n", "report", "/bin/bash", "-c"]

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_ENV=production
ENV FLASK_APP=main.py

# 运行Flask应用
CMD ["conda", "run", "-n", "report", "flask", "run", "--host=0.0.0.0"]