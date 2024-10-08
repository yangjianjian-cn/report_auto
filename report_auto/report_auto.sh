#!/bin/bash

# 定义启动命令
start_command="nohup gunicorn -k uvicorn.workers.UvicornWorker -w 3 -b 0.0.0.0:5000 main:main --timeout 300 > gunicorn_output.log 2>&1 & "

# 查找名为 "main:main" 的进程
process=$(ps -ef | grep 'main:main' | grep -v 'grep')

# 检查是否有匹配的进程
if [ -z "$process" ]; then
    # 如果没有找到进程，则启动
    echo "Starting the process: main:main"
    eval "$start_command"
else
    # 提取 PID
    pid=$(echo $process | awk '{print $2}')
    
    # 终止进程
    if kill $pid; then
        echo "Process with PID $pid has been terminated."
    else
        echo "Failed to terminate the process with PID $pid. Trying with -9..."
        if kill -9 $pid; then
            echo "Process with PID $pid has been forcefully terminated."
        else
            echo "Failed to forcefully terminate the process with PID $pid."
        fi
    fi
fi
