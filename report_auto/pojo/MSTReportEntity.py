class MSTReportEntity:
    def __init__(self, id=None, client_ip=None, csv_file_name=None, operator_rslt=None, test_type=None, total_num=None):
        self.id = id  # 如果是查询，则需要提供 id
        self.client_ip = client_ip
        self.csv_file_name = csv_file_name
        self.operator_rslt = operator_rslt
        self.test_type = test_type
        self.total_num = total_num

    def to_dict(self):
        """将对象转换为字典，用于插入操作"""
        return {k: v for k, v in self.__dict__.items() if v is not None and k != 'id'}

    def from_dict(cls, data):
        """从字典创建对象，用于查询结果转换"""
        return cls(**data)
