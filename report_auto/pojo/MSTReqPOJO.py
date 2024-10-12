#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"


class ReqPOJO:
    def __init__(self, dat_path=None, output_path=None, csv_path=None, test_team=None,
                 test_scenario=None, test_area=None, template_path=None, template_name=None, doc_output_name=None,
                 redis_connector=None, u_files=None):
        self.dat_path = dat_path
        self.output_path = output_path
        self.csv_path = csv_path
        self.test_team = test_team
        self.test_scenario = test_scenario
        self.test_area = test_area
        self.template_path = template_path
        self.template_name = template_name
        self.doc_output_name = doc_output_name
        self.redis_connector = redis_connector
        self.u_files = u_files
