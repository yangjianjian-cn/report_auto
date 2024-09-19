__coding__ = "utf-8"
import pandas as pd

# 创建 DataFrame
data = {
    'Tra_numGear': [0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 5, 0, 0, 0, 1, 1, 1],
    'Gbx_stGearShftDet': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
}

fault_detection_df = pd.DataFrame(data)

# 打印 DataFrame
print(fault_detection_df)

# 筛选出 Tra_numGear 从0变为1的部分
transition_rows = fault_detection_df[(fault_detection_df['Tra_numGear'] == 0) | (fault_detection_df['Tra_numGear'] == 1)]

# 获取 Gbx_stGearShftDet 的值
gear_shift_values_when_gear_1 = transition_rows['Gbx_stGearShftDet'].values
print("\n当 Tra_numGear 为1时，Gbx_stGearShftDet 的值为:")
print(gear_shift_values_when_gear_1)

# 分析 Tra_numGear 从0变为1时的变化
# 找到 Tra_numGear 从0变为1的第一个位置
first_transition_index = transition_rows.index[transition_rows['Tra_numGear'] == 1][0]

# 检查变化前后的值
previous_value = transition_rows.loc[first_transition_index - 1, 'Gbx_stGearShftDet']
current_value = transition_rows.loc[first_transition_index, 'Gbx_stGearShftDet']

print(f"\n在 Tra_numGear 从0变为1时的变化:")
print(f"变化前 Gbx_stGearShftDet 的值: {previous_value}")
print(f"变化后 Gbx_stGearShftDet 的值: {current_value}")

# 检查 Tra_numGear 为2及以上时的变化
higher_gear_df = fault_detection_df[fault_detection_df['Tra_numGear'] >= 2]
print("\nTra_numGear 为2及以上时的变化:")
print(higher_gear_df)