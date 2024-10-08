__coding__ = "utf-8"

from datetime import datetime

import pytz


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


def getCurDateTime():
    # 获取当前的 UTC 时间
    utc_now = datetime.utcnow()

    # 创建一个 UTC 时区对象，并将当前时间标记为 UTC 时间
    utc_zone = pytz.utc
    utc_now = utc_zone.localize(utc_now)

    # 创建一个北京时区对象
    beijing_tz = pytz.timezone('Asia/Shanghai')

    # 将当前时间转换为北京时间
    beijing_now = utc_now.astimezone(beijing_tz)
    return beijing_now


# 调用函数
# formatted_beijing_now = getCurDateTime().strftime('%Y-%m-%d %H:%M:%S')
# print("当前在北京时区的日期和时间：", formatted_beijing_now)
