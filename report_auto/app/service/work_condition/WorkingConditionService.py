from typing import Dict, List

from app import db_pool
from tools.utils.DBOperator import query_table_sampling


def work_condition_datas(column_list: list[str], selected_ids: list[int]):
    columns: str = ','.join(item['label_alias_name'] for item in column_list)
    if 'timestamps' not in columns:
        columns = columns + ',timestamps '

    file_ids_str_for_query = ', '.join(map(str, selected_ids))

    result_dicts: list[dict] = query_table_sampling(db_pool, columns, file_ids_str_for_query)

    work_condition_dict: Dict[str, List] = {
        col: [row[col] for row in result_dicts] for col in result_dicts[0].keys()
    }
    return work_condition_dict
