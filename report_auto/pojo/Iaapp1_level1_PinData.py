#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

'''
result
self.result = result
'''
class PinData:
    result = ''
    def __init__(self, column1, pin_no, pin, short_name, long_name, information_hints, device_doc, level1,
                 checked_values,
                 preparation,
                 stimulation, measurements):
        self.column1 = column1
        self.pin_no = pin_no
        self.pin = pin
        self.short_name = short_name
        self.long_name = long_name
        self.information_hints = information_hints
        self.device_doc = device_doc
        self.level1 = level1
        self.checked_values = checked_values
        self.preparation = preparation
        self.stimulation = stimulation
        self.measurements = measurements
        # 添加 result 属性并设置默认值
        # self.result = None

# Create an instance of the object
# my_pin_data = PinData(
#     pin_no='1',
#     pin='PIN1',
#     short_name='ShortPin1',
#     long_name='This is a very long name for PIN1',
#     information_hints='Some information hints here',
#     device_doc='Device documentation link',
#     checked_values='Values to be checked',
#     preparation='Preparation steps',
#     stimulation='Stimulation description',
#     measurements='Measurement details',
#     result='Test result'
# )
