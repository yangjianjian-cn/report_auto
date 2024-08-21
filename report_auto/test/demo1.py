import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Qt5Agg')  # TkAgg 或者 'Qt5Agg'

import numpy as np
import pandas as pd

# 创建数据
dates = pd.date_range(start='2024-08-01', periods=30, freq='D')
temperature = np.random.normal(loc=25, scale=5, size=len(dates))
humidity = np.random.normal(loc=50, scale=10, size=len(dates))

# 创建图表
fig, ax1 = plt.subplots()

# 在左侧y轴上绘制温度数据
color = 'tab:red'
ax1.set_xlabel('Date')
ax1.set_ylabel('Temperature (°C)', color=color)
ax1.plot(dates, temperature, color=color, label='Temperature')
ax1.tick_params(axis='y', labelcolor=color)

# 创建第二个y轴
ax2 = ax1.twinx()
color = 'tab:blue'
ax2.set_ylabel('Humidity (%)', color=color)
ax2.plot(dates, humidity, color=color, label='Humidity')
ax2.tick_params(axis='y', labelcolor=color)

# 添加图例
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')

# 设置图表标题
plt.title('Temperature and Humidity over Time')

# 调整日期格式
fig.autofmt_xdate()

# 显示图表
plt.show()
