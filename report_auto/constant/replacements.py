#!/usr/bin/env python
def brake_override_accelerator_replacements(brk_st=" ", app_bplabrk=" ", app_runflt=" ", app_r=" ",
                                            result=" ", criterion=" ", error_time="", ispass=" ", isfail=" ",
                                            total_time_spent=None):
    if total_time_spent is not None:
        error_time = f"{total_time_spent:.2f}" if not error_time else error_time
        boa_emrt = '√' if total_time_spent < 1000 and ispass == '√' else ''
        criterion = " " if not criterion else boa_emrt

    replacements = {
        "{1}": brk_st,
        "{2}": app_bplabrk,
        "{3}": app_runflt,
        "{4}": app_r,
        "{5}": result,
        "{6}": criterion,
        "{7}": error_time,
        "{8}": ispass,
        "{9}": isfail
    }
    return replacements


def main_brake_plausibility_check_replacements(brk_stmn="", dfc_brkplauschk="", brk_st="", is_dfc_brkplauschk="",
                                               is_dfc_brknpl="",
                                               is_pass="", is_fail="" ):
    replacements = {
        "{1}": brk_stmn,
        "{2}": dfc_brkplauschk,
        "{3}": brk_st,
        "{4}": "",
        "{5}": is_dfc_brkplauschk,
        "{6}": is_dfc_brknpl,
        "{7}": is_pass,
        "{8}": is_fail
    }
    return replacements


def redundant_brake_plausibility_check_replacements(err_msg: str):
    t_7 = ''
    t_8 = ''
    if str:
        t_8 = '√'
    else:
        t_7 = '√'
    replacements = {
        "{1}": "√",
        "{2}": "√",
        "{3}": "√",
        "{4}": " ",
        "{5}": "√",
        "{6}": "√",
        "{7}": t_7,
        "{8}": t_8
    }
    return replacements


def neutral_gear_sensor_plausibility_replacements(gbx_stnpos=' ', gbx_stgearshftdet=' ', dfc_gbxnposnpl='', is_pass=' ',
                                                  is_fail=''):
    replacements = {
        "{1}": gbx_stnpos,
        "{2}": gbx_stgearshftdet,
        "{3}": " ",
        "{4}": dfc_gbxnposnpl,
        "{5}": is_pass,
        "{6}": is_fail
    }
    return replacements


def plausibility_check_of_clth_stuck_top_replacements(clth_st_0: str = " ", is_not_equ: str = " ",
                                                      dfc_clthnplopn: str = " ", is_pass=" ", is_fail=" "):
    replacements = {
        "{1}": clth_st_0,
        "{2}": is_not_equ,
        "{3}": " ",
        "{4}": dfc_clthnplopn,
        "{5}": " ",
        "{6}": is_pass,
        "{7}": is_fail
    }
    return replacements


def plausibility_check_of_clth_stuck_bottom_replacements(clth_st_0: str = " ", clth_bautostrtenacond: str = " ",
                                                         is_not_equ=" ", clth_bclthplauserr=" ", dfc_clthplauschk=" ",
                                                         is_pass=" ", is_fail=" "):
    replacements = {
        "{1}": clth_st_0,
        "{2}": clth_bautostrtenacond,
        "{3}": is_not_equ,
        "{4}": clth_bclthplauserr,
        "{5}": " ",
        "{6}": dfc_clthplauschk,
        "{7}": is_pass,
        "{8}": is_fail
    }
    return replacements
