$(document).ready(function () {
    $('#select0').change(function () {
        var projectFile = $(this).val();
        if (projectFile) {
            $.ajax({
                url: '/report/iotest/scenario',
                data: {
                    'projectFile': projectFile
                },
                success: function (response) {
                    // 清空 select1
                    $('#select1').empty();
                    // 添加默认选项
                    $('#select1').append('<option value="">--Scenario--</option>');
                    // 添加新的选项
                    $.each(response.record_list, function (index, module_obj) {
                        $('#select1').append($('<option></option>').attr('value', module_obj.moduleName).text(module_obj.moduleName));
                    });
                    // 如果有需要，调用 updateSelectCheck2 函数
                    updateSelectCheck2();
                }
            });
        } else {
            // 如果没有选择项目，清空 select1
            $('#select1').empty().append('<option value="">--Scenario--</option>');
        }
    });
});

function updateSelectCheck2() {
    const select0 = document.getElementById("select0");
    const select1 = document.getElementById("select1");
    const select2 = document.getElementById("select2");

    // 清空select2
    while (select2.firstChild) {
        select2.removeChild(select2.firstChild);
    }

    const project_file = select0.value;
    const module_name = select1.value;
    const jsonData = {"project_file": project_file, "module_name": module_name}
    $.ajax({
        url: '/report/2/dict_type/items',
        type: 'POST',
        contentType: 'application/json',  // 设置请求头
        data: JSON.stringify(jsonData),  // 发送的数据
        success: function (response) {
            // 遍历response并填充select2
            response.forEach(item => {
                let item_val = item.item_value;
                let item_text = item.item_label;
                let slt_option = document.createElement("option");

                slt_option.value = item_text
                slt_option.text = '【' + item_val + '】 ' + item_text
                slt_option.setAttribute("data-label", item_val)
                select2.appendChild(slt_option);
            });
        },
        error: function (error) {
            layer.alert('Query failed! error message:' + JSON.stringify(error.error), {
                icon: 5,
                title: 'Query results'
            });
        }
    });
}
