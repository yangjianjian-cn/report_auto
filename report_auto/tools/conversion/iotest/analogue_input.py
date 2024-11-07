__coding__ = "utf-8"

from app import db_pool
from tools.utils.DBOperator import query_table


class IOTestDataInDB(object):
    # 查询test_area下test_scenario,需要得信号量
    def get_io_test_data(test_area: str, test_scenario: str) -> dict:
        query = '''
                    SELECT pin_no, hw_pin, short_name, long_name, device_encapsulation, checked_values,
                           preparation_1, measurements_1, checked_errors, preparation_2, measurements_2,
                           debouncing_healing, preparation_3, measurements_3, error_substitute, preparation_4,
                           measurements_4, detail_id
                    FROM io_test_checklist WHERE detail_id = (
                    SELECT detail_id
                    FROM tool_dictionary  td
                    JOIN tool_dictionary_detail tdd on td.dict_id = tdd.dict_id
                    WHERE td.dict_value = %s and td.dict_type = 'signal_type'
                    and tdd.item_value =  %s )
            '''
        params = (test_area, test_scenario)
        result_dicts: dict = query_table(db_pool, query=query, params=params)
        return result_dicts

    def csv_needed_columns(self, result_dicts: dict) -> set[str]:
        columns: set[str] = set()

        keys = [
            "measurements_1", "preparation_2", "measurements_2",
            "preparation_3", "measurements_3", "preparation_4", "measurements_4"
        ]

        # 使用列表推导式获取所有非空内容
        contents = [result_dicts.get(key) for key in keys if result_dicts.get(key)]

        # 将所有内容按行分割并添加到集合中
        for content in contents:
            columns.update(content.splitlines())

        return columns
