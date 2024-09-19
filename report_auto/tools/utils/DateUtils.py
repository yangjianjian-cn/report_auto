__coding__ = "utf-8"


def seconds_to_minutes(seconds):
    # 将秒转换为分钟，保留两位小数
    minutes = round(seconds / 60, 1)
    return minutes

# seconds = 119.8607423
# minutes = seconds_to_minutes(seconds)
# print(minutes)
