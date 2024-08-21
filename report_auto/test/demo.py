import matplotlib.pyplot as plt
import numpy as np

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')  # TkAgg 或者 'Qt5Agg'

import pandas as pd
pd.set_option('future.no_silent_downcasting', True)


# 创建一些示例数据
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# 创建第一个图例的数据
line1, = plt.plot(x, y1, label='Sine', color='blue')
line2, = plt.plot(x, y2, label='Cosine', color='red')

# 创建第二个图例的数据
scatter1 = plt.scatter([2, 7], [np.sin(2), np.sin(7)], label='Max Values', color='green', s=100)

# 第一个图例
plt.legend(handles=[line1, line2], loc='upper right', title='Trigonometric Functions')

# 第二个图例
plt.legend(handles=[scatter1], loc='lower right', title='Special Points')

plt.show()

