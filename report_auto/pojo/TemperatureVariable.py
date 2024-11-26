__coding__ = "utf-8"


class TemperatureVariable:
    def __init__(self, measurement_file_id, quantitative_variable, statistical_variable, remark):
        self.measurement_file_id = measurement_file_id
        self.quantitative_variable = quantitative_variable
        self.statistical_variable = statistical_variable
        self.remark = remark
