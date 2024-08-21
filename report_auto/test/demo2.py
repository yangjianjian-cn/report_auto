import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Qt5Agg')  # TkAgg 或者 'Qt5Agg'

import numpy as np
import pandas as pd

# 创建数据
dates = pd.date_range(start='2024-08-01', periods=30, freq='D')
data1 = np.random.normal(loc=25, scale=5, size=len(dates))  # 数据集1
data2 = np.random.normal(loc=30, scale=5, size=len(dates))  # 数据集2
data3 = np.random.normal(loc=35, scale=5, size=len(dates))  # 数据集3
data4 = np.random.normal(loc=50, scale=10, size=len(dates))  # 数据集4
data5 = np.random.normal(loc=60, scale=10, size=len(dates))  # 数据集5

# 创建图表
fig, ax1 = plt.subplots()

# 在左侧y轴上绘制前三个数据集
colors = ['tab:red', 'tab:orange', 'tab:green']
ax1.set_xlabel('Date')
ax1.set_ylabel('Data 1 Values', color=colors[0])
ax1.plot(dates, data1, color=colors[0], linestyle='-', marker='o', label='Data 1')
ax1.tick_params(axis='y', labelcolor=colors[0])

# 创建第二个左侧y轴
ax2 = ax1.twinx()
ax2.spines.right.set_position(("axes", 1.1))  # 将第二个y轴移动到右侧
ax2.set_ylabel('Data 2 Values', color=colors[1])
ax2.plot(dates, data2, color=colors[1], linestyle='--', marker='s', label='Data 2')
ax2.tick_params(axis='y', labelcolor=colors[1])

# 创建第三个左侧y轴
ax3 = ax1.twinx()
ax3.spines.right.set_position(("axes", 1.2))  # 将第三个y轴移动到右侧
ax3.set_ylabel('Data 3 Values', color=colors[2])
ax3.plot(dates, data3, color=colors[2], linestyle=':', marker='^', label='Data 3')
ax3.tick_params(axis='y', labelcolor=colors[2])

# 创建右侧的第一个y轴
ax4 = ax1.twinx()
ax4.spines.right.set_position(("axes", 1.3))  # 将右侧的第一个y轴移动到更远的右侧
color = 'tab:blue'
ax4.set_ylabel('Data 4 Values', color=color)
ax4.plot(dates, data4, color=color, linestyle='-', marker='v', label='Data 4')
ax4.tick_params(axis='y', labelcolor=color)

# 创建右侧的第二个y轴
ax5 = ax1.twinx()
ax5.spines.right.set_position(("axes", 1.4))  # 将右侧的第二个y轴移动到最右侧
color = 'tab:purple'
ax5.set_ylabel('Data 5 Values', color=color)
ax5.plot(dates, data5, color=color, linestyle='--', marker='p', label='Data 5')
ax5.tick_params(axis='y', labelcolor=color)

# 添加图例
ax1.legend(loc='upper left')
ax2.legend(loc='upper center')
ax3.legend(loc='upper right')
ax4.legend(loc='lower right')
ax5.legend(loc='lower left')

# 设置图表标题
plt.title('Multiple Data Sets Over Time with Multiple Y-axes')

# 调整日期格式
fig.autofmt_xdate()

# 显示图表
plt.show()