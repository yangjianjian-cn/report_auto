__coding__ = "utf-8"

import datetime

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


def get_current_datetime_yyyyMMddHHmmssSSS():
    # 获取当前日期和时间
    current_datetime = datetime.datetime.now()

    # 格式化日期时间为 YYYYMMDDHHmmssSSS 的形式
    # 注意：使用 '%f' 表示微秒，这里取前三位表示毫秒
    formatted_datetime = current_datetime.strftime('%Y%m%d%H%M%S%f')[:-3]

    return formatted_datetime


def getCurDateTime():
    # 获取当前的 UTC 时间
    utc_now = datetime.datetime.utcnow()

    # 创建一个 UTC 时区对象，并将当前时间标记为 UTC 时间
    utc_zone = pytz.utc
    utc_now = utc_zone.localize(utc_now)

    # 创建一个北京时区对象
    beijing_tz = pytz.timezone('Asia/Shanghai')

    # 将当前时间转换为北京时间
    beijing_now = utc_now.astimezone(beijing_tz)

    # 返回北京时间
    return beijing_now
