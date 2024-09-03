import re
from enum import Enum

"""模板名称=dat/csv文件名"""


class TestCaseType(Enum):
    brake_override_accelerator = '1app_pl_br_1'
    main_brake_plausibility_check = '2brk_04'
    redundant_brake_plausibility_check = '3brk_05'
    neutral_gear_sensor_plausibility_check = '4ngs_06'
    plausibility_check_of_clth_stuck_top = '5clth_05'
    plausibility_check_of_clth_stuck_bottom = '6clth_06'
    IOTest_Man_Tmplt = 'IO_Test'


def fuzzy_match_test_case_type(pattern):
    """
    根据提供的模式pattern模糊匹配TestCaseType枚举成员。

    :param pattern: 用于匹配的模式字符串。
    :return: 匹配的枚举成员列表。
    """
    # 编译正则表达式模式以提高性能
    regex = re.compile(pattern, re.IGNORECASE)
    matched_members = [member for member in TestCaseType if regex.search(member.value)]
    first_matched_member = matched_members[0] if matched_members else None
    return first_matched_member


# # 示例使用
# search_pattern = 'brk'  # 模糊匹配模式
# matched_cases = fuzzy_match_test_case_type(search_pattern)
# for case in matched_cases:
#     print(f"{case.name}: {case.value}")
