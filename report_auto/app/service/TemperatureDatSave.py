import logging

from asammdf import MDF
from asammdf.blocks.utils import MdfException
from flask import jsonify

from app.service.ToolCommonService import get_chip_dict, create_rename_mapping
from tools.utils.DBOperator import batch_insert_data, alter_table_add_columns, create_table

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# 数据接收与验证
def validate_request(data):
    last_id = data.get('save_file_id', '')
    if not last_id:
        return None, jsonify({'generate_report_failed': 'File number acquisition exception'})
    return last_id, None


# 数据采集准备
def prepare_data_collection(last_id, measure_file_path):
    # 采集量
    selected_columns_dict: list[dict] = get_chip_dict(last_id)
    if not selected_columns_dict:
        return None, jsonify({'generate_report_failed': "unconfigured acquisition volume"})

    # 已配置[label_name]
    selected_columns: list[str] = [d['label_name'] for d in selected_columns_dict]
    logging.info(f"已配置[label_name]:{selected_columns}")

    try:
        mdf = MDF(measure_file_path)
    except MdfException as e:
        logging.error(f"Error loading MDF file: {e}")
        return None, jsonify({'generate_report_failed': str(e)})

    # 文件中的采集信号列
    channels_db_keys = mdf.channels_db.keys()
    logging.info(f"[信号量]待采集:{channels_db_keys}")

    # 采用最长匹配原则，去匹配文件中的信号列
    existing_columns: list[str] = list(set(col for col in selected_columns if col in channels_db_keys))

    # 创建新的字典
    label_to_alias_dict = {item['label_name']: item['label_alias_name'] for item in selected_columns_dict}
    # 过滤字典，只保留 existing_columns 中存在的项
    filtered_label_to_alias_dict = {key: label_to_alias_dict[key] for key in existing_columns if
                                    key in label_to_alias_dict}

    if "TECU_t" in channels_db_keys:
        # existing_columns.append("TECU_t")
        filtered_label_to_alias_dict["TECU_t"] = "TECU_t"
    elif "TECU_tRaw" in channels_db_keys:
        # existing_columns.append("TECU_tRaw")
        filtered_label_to_alias_dict["TECU_tRaw"] = "TECU_t"

    logging.info(f"[信号量]可采集:{filtered_label_to_alias_dict}")

    return filtered_label_to_alias_dict, mdf


# 实际数据采集
def collect_data(mdf, existing_columns: list[str]):
    try:
        df = mdf.to_dataframe(channels=existing_columns)
    except MdfException as e:
        logging.error(f"Error converting to DataFrame: {e}")
        return None, jsonify({'generate_report_failed': str(e)})
    return df, None


# 数据清洗
def clean_data(df, filtered_label_to_alias_dict: dict[str, str]):
    # def rename_columns(column_name):
    #     if '\\' in column_name:
    #         return column_name.split('\\')[0]
    #     else:
    #         return column_name
    #
    # def get_rename_mapping(columns: list[str]):
    #     logging.debug(f"get_rename_mapping:{columns}")
    #
    #     rename_mapping: dict = create_rename_mapping(columns)
    #
    #     # 特殊情况处理：TECU_tRaw 列，别名为 TECU_t
    #     if 'TECU_t' not in columns and 'TECU_tRaw' in columns:
    #         rename_mapping['TECU_tRaw'] = 'TECU_t'
    #     return rename_mapping

    # df.columns = [rename_columns(col) for col in df.columns]
    df.columns: list[str] = list(filtered_label_to_alias_dict.keys())

    # column_names = df.columns.tolist()
    # rename_mapping = get_rename_mapping(column_names)
    rename_mapping = filtered_label_to_alias_dict
    logging.info(f"信号列和数据库列映射:{rename_mapping}")

    df.rename(columns=rename_mapping, inplace=True)  # 重命名列名

    df.sort_values(by='timestamps', inplace=True)
    logging.info(f"数据排序:{len(df)}")

    df.drop_duplicates(keep='first', inplace=True)
    logging.info(f"数据去重:{len(df)}")

    return df,rename_mapping


# 数据存储准备
def prepare_data_storage(db_pool, table_name, df, last_id, file_source, rename_mapping):
    params = {'file_id': last_id, 'source': file_source}
    c_ret_msg, columns_in_db = create_table(db_pool, table_name=table_name, df=df)
    if c_ret_msg != 'success':
        return None, jsonify({'generate_report_failed': c_ret_msg})

    missing_columns = [value for value in rename_mapping.values() if value not in columns_in_db]
    logging.info(f"表{table_name}添加列:{missing_columns}")
    if missing_columns:
        op_flag, op_msg = alter_table_add_columns(db_pool, table=table_name, columns=missing_columns,
                                                  column_type="double")
        logging.info(f"{op_flag},{op_msg}")

    return params, columns_in_db


# 数据存储
def store_data(db_pool, table_name, params, df):
    i_ret_msg = batch_insert_data(db_pool, table_name=table_name, params=params, df=df)
    if i_ret_msg != 'success':
        return jsonify({'generate_report_failed': i_ret_msg})
    return jsonify({'generate_report_failed': ''})


# 主流程
def main_process(data, measure_file_path, db_pool, table_name, file_source):
    last_id, error_response = validate_request(data)
    if error_response:
        return error_response

    existing_columns, mdf = prepare_data_collection(last_id, measure_file_path)
    if error_response:
        return error_response

    df, error_response = collect_data(mdf, existing_columns)
    if error_response:
        return error_response

    df, rename_mapping = clean_data(df)

    params, error_response = prepare_data_storage(db_pool, table_name, df, last_id, file_source, rename_mapping)
    if error_response:
        return error_response

    return store_data(db_pool, table_name, params, df)
