from pojo.MSTReqPOJO import ReqPOJO
from tools.conversion.brake_plausibility_check_parser import brake_plausibility_check


def redundant_brake_plausibility_check(req_data: ReqPOJO):
    output_path = brake_plausibility_check(req_data, brkStMn=False, brkStRed=True,tplt_type='redundant_brake_plausibility_check')
    return output_path
