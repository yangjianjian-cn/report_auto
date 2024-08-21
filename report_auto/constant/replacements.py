#!/usr/bin/env python
def brake_override_accelerator_replacements(total_time_spent: float):
    boa_emrt = '√' if total_time_spent < 1000 else ''
    replacements = {
        "{1}": "√",
        "{2}": "√",
        "{3}": "√",
        "{4}": "√",
        "{5}": "√",
        "{6}": f"{boa_emrt}",
        "{7}": f"{total_time_spent:.2f}",
        "{8}": "√",
        "{9}": ""
    }
    return replacements


def main_brake_plausibility_check_replacements(total_time_spent: float):
    replacements = {
        "{1}": "√",
        "{2}": "√",
        "{3}": "√",
        "{4}": "√",
        "{5}": "√",
        "{6}": f"{total_time_spent:.2f}",
        "{7}": "√",
        "{8}": "√"
    }
    return replacements
