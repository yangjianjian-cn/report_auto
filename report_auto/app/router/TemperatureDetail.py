__coding__ = "utf-8"

import logging

from flask import request, render_template

from app.router import temperature_bp
from app.service.TemperatureDataService import get_measurement_file_list, \
    process_temperature_data
from app.service.ToolCommonService import chip_dict_in_sql
from tools.utils.HtmlGenerator import generate_select_options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@temperature_bp.route('/details', methods=['GET'])
def temperature_details():
    selected_ids = []
    fileId = request.args.get('fileId')

    # 1.获取测量文件列表
    try:
        measurement_file_list = get_measurement_file_list(fileId=fileId)
    except Exception as e:
        return render_template('error.html', failure_msg=f'{e}')

    if measurement_file_list is None or len(measurement_file_list) == 0:
        return render_template('error.html', failure_msg='Please upload the file first.')

    logging.info(f"获得测量文件:{len(measurement_file_list)}")
    # 定量变量(离散图，求两个变量的线性关系)
    filtered_files: list = []
    if fileId:
        selected_ids = [int(id) for id in fileId.split(',')]
        filtered_files = [file for file in measurement_file_list if file['id'] in selected_ids]
    else:
        selected_ids.append(measurement_file_list[0].get('id'))
        filtered_files.append(measurement_file_list[0])

    special_columns_str = filtered_files[0].get('quantitative_variable', '')
    quantitative_variable_list = [special_columns_str]

    measurement_source = filtered_files[0].get('source')
    oem = filtered_files[0].get("oem")
    project_type: list = [oem]

    logging.info(f"定量变量:{quantitative_variable_list}")
    logging.info(f"燃料类型:{measurement_source}")
    logging.info(f"测量项目:{project_type}")
    logging.info(f"观测文件:{selected_ids}")

    # 2. 获取芯片字典列表
    r_chip_dict: list[dict] = chip_dict_in_sql(selected_ids=selected_ids, project_type=project_type)
    kv_chip_dict: dict = {item['measured_variable']: item['chip_name'] for item in r_chip_dict}
    measured_variables_list: list[str] = [item['measured_variable'] for item in r_chip_dict]
    logging.info(f"可观测信号量:{measured_variables_list}")

    if not special_columns_str or len(measured_variables_list) == 0:
        return render_template('error.html', failure_msg='Observation variable not configured!')

    # 离散图和折线图
    temperature_legend_list, temperature_line_dict, temperature_scatter_list = process_temperature_data(
        measured_variables_list=measured_variables_list,
        quantitative_variable_list=quantitative_variable_list,
        selected_ids=selected_ids,
        kv_chip_dict=kv_chip_dict
    )

    # 下拉复选框
    multi_select_html = generate_select_options(get_measurement_file_list(fileId=None))

    # 渲染页面
    return render_template('temperature_details_again.html',
                           temperature_legend_list=temperature_legend_list,
                           temperature_scatter_list=temperature_scatter_list,
                           temperature_line_dict=temperature_line_dict,

                           multi_select_html=multi_select_html,
                           init_selected_files=selected_ids,
                           measurement_source=measurement_source,
                           quantitative_variable=special_columns_str
                           )
