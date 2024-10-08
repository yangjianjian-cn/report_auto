__coding__ = "utf-8"


def generate_select_options(measurement_files,selected_ids=None):
    """
    生成 <select> 控件的 HTML 代码。

    :param measurement_files: 包含 MeasurementFile 对象的列表。
    :param selected_ids: 可选参数，指定哪些选项应该是预选中的。
    :return: 生成的 HTML 字符串。
    """
    selected_ids = selected_ids or []
    select_html = '<select id="example-multiple-optgroups" multiple="multiple" class="bg-warning" tabindex="-1">\n'
    select_html += '    <optgroup label="HTM Files">\n'

    for mf in measurement_files:
        file_id = mf.get('id')
        file_name = mf.get('file_name')
        selected_attr = 'selected="selected"' if file_id in selected_ids else ''
        select_html += f'        <option value="{file_id}" {selected_attr}>{file_name}</option>\n'
    select_html += '    </optgroup>\n'
    select_html += '</select>\n'

    return select_html
