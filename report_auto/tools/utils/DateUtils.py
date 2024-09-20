__coding__ = "utf-8"

import datetime


def seconds_to_minutes(seconds):
    # 将秒转换为分钟，保留两位小数
    minutes = round(seconds / 60, 1)
    return minutes


def get_current_date_yyyyMMdd():
    # 获取当前日期
    current_date = datetime.date.today()

    # 格式化日期为 YYYYMMDD 的形式
    formatted_date = current_date.strftime('%Y%m%d')

    return formatted_date