import pandas as pd

pd.set_option('future.no_silent_downcasting', True)

import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')  # TkAgg 或者 'Qt5Agg'

# 假设这是你的数据框
data = {
    'timestamps': [0, 1, 2, 3, 4, 5],
    'Brk_st': [10, 20, 30, 40, 50, 60],
    'APP_bPlaBrk': [150, 250, 350, 450, 550, 650],
    'APP_rUnFlt': [5, 15, 25, 35, 45, 55],
    'APP_r': [100, 200, 300, 400, 500, 600],
    'VehV_v': [50, 60, 70, 80, 90, 100],
    'Epm_nEng': [120, 220, 320, 420, 520, 620],
    'CEngDsT_t': [30, 40, 50, 60, 70, 80],
    'Tra_numGear': [1, 2, 3, 4, 5, 6],
    'DFES_numDFC_[0]': [80, 90, 100, 110, 120, 130]
}
fault_detection_df = pd.DataFrame(data)

# 找出每个信号的最大值
max_values = fault_detection_df.drop(columns=['timestamps']).max()

# 分类信号
small_y_axis_signals = [col for col in max_values.index if max_values[col] <= 100]
large_y_axis_signals = [col for col in max_values.index if max_values[col] > 100]

# 动态设置第二个Y轴的范围
if large_y_axis_signals:
    max_large_value = max_values[large_y_axis_signals].max()
else:
    max_large_value = 100  # 如果没有大值信号，设置一个默认值

# 创建一个新的图形
fig, ax1 = plt.subplots(figsize=(10, 6))

# 绘制第一个Y轴的信号
for signal in small_y_axis_signals:
    ax1.plot(fault_detection_df['timestamps'], fault_detection_df[signal], label=signal)
ax1.set_xlabel('Timestamps (s)')
ax1.set_ylabel('Small Y Axis Values', color='blue')
ax1.set_ylim(0, 100)  # 设置第一个Y轴的范围从0到100
ax1.tick_params(axis='y', labelcolor='blue')

# 创建第二个Y轴
if large_y_axis_signals:
    ax2 = ax1.twinx()
    for signal in large_y_axis_signals:
        ax2.plot(fault_detection_df['timestamps'], fault_detection_df[signal], label=signal, linestyle='--')
    ax2.set_ylabel('Large Y Axis Values', color='red')
    ax2.set_ylim(100, max_large_value)  # 动态设置第二个Y轴的范围
    ax2.yaxis.set_major_locator(plt.MultipleLocator(100))  # 设置第二个Y轴的刻度间隔为100
    ax2.tick_params(axis='y', labelcolor='red')

    # 设置第二个Y轴的位置
    ax2.spines['right'].set_position(('outward', 60))  # 可以调整数值来改变位置
    ax2.yaxis.set_label_coords(1.15, 0.5)  # 调整Y轴标签的位置

# 添加图例
if small_y_axis_signals:
    ax1.legend(loc='upper left')  # 图例显示在左边

if large_y_axis_signals:
    ax2.legend(loc='upper right')  # 图例显示在右边

# 设置图表标题
ax1.set_title('Signals Over Time')

# 调整布局
plt.tight_layout()

# 保存图表到文件
plt.savefig('output_chart.png')

# 关闭图形
plt.close(fig)
