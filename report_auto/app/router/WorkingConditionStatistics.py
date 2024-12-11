import logging

from flask import render_template, request

from app.router import temperature_bp
from app.service.TemperatureDataService import get_measurement_file_list, s_get_non_empty_column_names
from app.service.ToolCommonService import get_tool_parameters
from app.service.work_condition.WorkingConditionService import work_condition_datas
from constant.ToolConstants import ToolConstants
from tools.utils.HtmlGenerator import generate_select_options


@temperature_bp.route('/working_condition', methods=['GET'])
def working_condition():
    work_condition_dict_line: dict[str, list] = {}
    temperature_legend_list: list[str] = []
    try:
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

        filtered_files: list = []
        if fileId:
            selected_ids = [int(id) for id in fileId.split(',')]
        else:
            selected_ids.append(measurement_file_list[0].get('id'))
            filtered_files.append(measurement_file_list[0])

        logging.info(f"观测文件:{selected_ids}")

        # 2. 查询列
        param_val: str = get_tool_parameters(ToolConstants.WORK_CONDITION)
        param_list: list = param_val.split(',')
        # 创建字典列表
        r_chip_dict: dict = [{"label_alias_name": param, "chip_name": param} for param in param_list]

        column_list: list[dict] = s_get_non_empty_column_names(file_ids=selected_ids, r_chip_dict=r_chip_dict)
        if r_chip_dict is None or len(r_chip_dict) == 0:
            return render_template('error.html', failure_msg='Empty File...')

        work_condition_dict: dict[str, list] = work_condition_datas(column_list, selected_ids)
        # temperature_legend_list: list[str] = list(work_condition_dict.keys())

        # 4.文件下拉复选框
        multi_select_html = generate_select_options(get_measurement_file_list(fileId=None))

    except Exception as e:
        logging.error(f'查询异常:{e}')
        return render_template('error.html', failure_msg=f'{e}')

    return render_template('working_condition.html',
                           multi_select_html=multi_select_html,
                           work_condition_dict_line=work_condition_dict)
