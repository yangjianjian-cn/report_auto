__coding__ = "utf-8"

import logging
from collections import defaultdict

from flask import request, render_template

from app.router import temperature_bp
from app.service.TemperatureDataService import get_measurement_file_list
from app.service.TemperatureOverviewService import relative_difference, temperature_duration
from app.service.ToolCommonService import chip_dict_in_sql
from tools.utils.HtmlGenerator import generate_select_options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@temperature_bp.route('/overview', methods=['GET'])
def temperature_overview():
    # 1.获取测量文件列表（网页上选择一个文件或多个)
    fileId: str = request.args.get('fileId')
    try:
        measurement_file_list = get_measurement_file_list(fileId=fileId)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    selected_ids = []
    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
        filtered_files = [file for file in measurement_file_list if file['id'] in selected_ids]

        statistical_variables_list: list = [file['statistical_variable'] for file in filtered_files if
                                            file['statistical_variable'] is not None]
        statistical_variables_str = statistical_variables_list[0]

        project_type: list[str] = [file['oem'] for file in filtered_files]

        measurement_source = filtered_files[0]['source']

    else:
        selected_ids.append(measurement_file_list[0].get('id'))
        filtered_files = measurement_file_list[0]

        statistical_variables_str: str = filtered_files['statistical_variable']
        project_type: list[str] = [filtered_files['oem']]

        measurement_source = filtered_files['source']

    if not statistical_variables_str:
        return render_template('error.html', failure_msg='Statistical variables not configured.')

    logging.info(f"统计量:{statistical_variables_str}")
    logging.info(f"燃料类型:{measurement_source}")
    logging.info(f"项目:{project_type}")
    logging.info(f"观测文件:{selected_ids}")

    chip_dict_list = chip_dict_in_sql(selected_ids=selected_ids, project_type=project_type)
    logging.info(f"电子元器件字典:{chip_dict_list}")

    # 创建一个字典来存储匹配结果
    statistical_variables_name_list: list[dict] = []
    statistical_variables_list = statistical_variables_str.split(",")
    for variable in statistical_variables_list:
        variable = variable.strip()
        matched_chip = next((chip for chip in chip_dict_list if chip['chip_name'] == variable), None)
        if matched_chip:
            statistical_variables_name_list.append(
                {'label_alias_name': matched_chip['label_alias_name'], 'chip_name': matched_chip['chip_name']})
        elif "TECU_t" == variable:
            statistical_variables_name_list.append({'label_alias_name': variable, 'chip_name': variable})

    grouped_variables = defaultdict(set)
    for item in statistical_variables_name_list:
        chip_name = item['chip_name']
        label_alias_name = item['label_alias_name']
        grouped_variables[chip_name].add(label_alias_name)

    # 将集合转换为列表
    grouped_variables_list: list = {chip: list(variables) for chip, variables in grouped_variables.items()}
    logging.info(f"统计量(名称:变量):{grouped_variables_list}")

    # 温度时长柱形图和饼状图
    """
        {
            'combined_time_diffs_tecut_dict': combined_time_diffs_tecut_dict,
            'combined_time_diffs_x3_dict': combined_time_diffs_x3_dict,
            'combined_time_diffs_x2_dict': combined_time_diffs_x2_dict,
            'total_minutes_tecut_f': total_minutes_tecut_f,
            'total_minutes_x3_f': total_minutes_x3_f,
            'total_minutes_x2_f': total_minutes_x2_f
       }
        time_diffs_tecut, total_minutes_tecut, time_diffs_tc1th9, total_minutes_tc1th9 
    """
    temperature_duration_dict: dict = temperature_duration(
        file_ids_int=selected_ids,
        max_workers=len(selected_ids), statistical_variables_dict=grouped_variables_list)

    # 温度阈值 和 相对温差
    chip_dict_list = relative_difference(selected_ids, chip_dict_list)
    chip_names = [chip['chip_name'] for chip in chip_dict_list]
    max_allowed_values = [chip['max_allowed_value'] for chip in chip_dict_list]
    max_temperature = [chip['max_temperature'] for chip in chip_dict_list]
    relative_difference_temperature = [-chip['relative_difference_temperature'] for chip in chip_dict_list]

    # 下拉多选框
    multi_select_html = generate_select_options(get_measurement_file_list(fileId=None))

    # 渲染页面
    return render_template('temperature_overview.html',
                           total_minutes_tecut=temperature_duration_dict.get("total_minutes_tecut_f"),
                           total_minutes_x3=temperature_duration_dict.get("total_minutes_x3_f"),
                           total_minutes_x2=temperature_duration_dict.get("total_minutes_x2_f"),

                           time_diffs_tecut=temperature_duration_dict.get("combined_time_diffs_tecut_dict"),
                           time_diffs_x3=temperature_duration_dict.get("combined_time_diffs_x3_dict"),
                           time_diffs_x2=temperature_duration_dict.get("combined_time_diffs_x2_dict"),

                           multi_select_html=multi_select_html,
                           init_selected_files=fileId,

                           chip_names=chip_names,
                           max_allowed_values=max_allowed_values,
                           max_temperature=max_temperature,
                           relative_difference_temperature=relative_difference_temperature,
                           measurement_source=measurement_source
                           )
