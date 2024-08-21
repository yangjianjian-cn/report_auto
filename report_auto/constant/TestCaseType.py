from enum import Enum

"""模板名称=dat/csv文件名"""


class TestCaseType(Enum):
    brake_override_accelerator = 'app_pl_br_1'
    main_brake_plausibility_check = 'brk_04'
    redundant_brake_plausibility_check = 'brk_05'
    neutral_gear_sensor_plausibility_check = 'ngs_06'
    plausibility_check_of_clth_stuck_top = 'clth_05'
    plausibility_check_of_clth_stuck_bottom = 'clth_06'


# 使用枚举类
# print(TestCaseType.brake_override_accelerator)
# print(type(TestCaseType.brake_override_accelerator))
# print(TestCaseType.brake_override_accelerator.value)
# print(TestCaseType.brake_override_accelerator.name)
