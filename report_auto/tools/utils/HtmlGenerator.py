__coding__ = "utf-8"

from collections import defaultdict


def generate_select_options(measurement_files, selected_ids=None):
    grouped_files = defaultdict(list)

    for file in measurement_files:
        oem = file['oem']
        grouped_files[oem].append(file)

    # 初始化选中的 ID 列表
    selected_ids = selected_ids or []

    # 使用列表来存储生成的 HTML 部分
    html_parts = ['<select id="example-multiple-optgroups" multiple="multiple" class="bg-warning" tabindex="-1">\n']

    for oem, files in grouped_files.items():
        html_parts.append(f'    <optgroup label="{oem}">\n')

        for mf in files:
            file_id = mf['id']
            file_name = mf['file_name']
            # selected_attr = 'selected="selected"' if file_id in selected_ids else ''
            # html_parts.append(f'        <option value="{file_id}" {selected_attr}>{file_name}</option>\n')
            # selected_attr = 'selected="selected"' if file_id in selected_ids else ''
            html_parts.append(f'        <option value="{file_id}">{file_name}</option>\n')

        html_parts.append('    </optgroup>\n')

    html_parts.append('</select>\n')

    # 最后用 join 方法将所有部分连接起来
    select_html = ''.join(html_parts)

    return select_html
