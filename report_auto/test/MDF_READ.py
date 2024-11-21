import pandas as pd
from asammdf import MDF


def read_mdf(filepath: str) -> pd.DataFrame:
    try:
        # 尝试加载MDF文件
        mdf = MDF(filepath)

        # 将MDF文件转换为pandas DataFrame
        df = mdf.to_dataframe()

        # 计算每个信号的最大值
        max_values = df.max(numeric_only=True)

        # 四舍五入，保留三位小数
        max_values_rounded = max_values.round(3)

        # 打印每个信号的最大值
        print("每个信号的最大值：")
        print(max_values_rounded)

        # 返回DataFrame
        return df

    except FileNotFoundError:
        print(f"错误：文件 {filepath} 不存在，请检查文件路径是否正确。")
    except Exception as e:
        print(f"读取文件 {filepath} 时发生错误：{str(e)}")


# 使用示例
df = read_mdf(r'C:\Users\Administrator\OneDrive\桌面\tmp\SANY_CE868_Highway_DS.dat')

# 如果函数执行成功，打印DataFrame的前几行以检查数据
if isinstance(df, pd.DataFrame):
    print(df.head())
else:
    print("未能成功读取文件为DataFrame。")
