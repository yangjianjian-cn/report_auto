$("#report_pro_text").on("dblclick", function () {
    $("#report_pro_text").empty()
})

// ---------- 生成报告 ----------
$("#report_generation").on("click", function () {
    var filenames = uploadedFileName.join(',');
    if (filenames == '') {
        layer.alert('请先上传文件', {icon: 5});
        return false;
    }

    $('#report_generation').prop('disabled', true);

    const selectedValue0 = $('#test_project_type_val').val();
    let selectedValue1 = $('#select1').val();
    let selectedValues2 = $('#select2').val();
    if (selectedValue1 == 'undefined' || selectedValue1 == undefined) {
        selectedValue1 = '';
    }

    if (selectedValues2 == 'undefined' || selectedValues2 == undefined) {
        selectedValues2 = ''
    }

    var test_project_type_id = $("#test_project_type_id").val()
    if ('2' == test_project_type_id) {
        if (selectedValue1 == '' || selectedValues2 == '') {
            layer.alert('请选择测试场景', {icon: 3})
            return false;
        }
    }

    const jsonData = JSON.stringify({
        "test_team": selectedValue0,
        "test_scenario": selectedValue1,
        "test_area": selectedValues2
    });

    var index = layer.load(0, {shade: false}); //0代表加载的风格，支持0-2

    // 生成报告
    $.ajax({
        url: '/generate_report',
        type: 'POST',
        dataType: 'json',
        data: jsonData,
        contentType: 'application/json; charset=utf-8',
        success: function (response) {
            report_success = true
            $("#report_pro_text").append("报告生成成功:<br/>" + response.generate_report_success)
            $('#report_generation').prop('disabled', false);
            layer.alert('报告生成成功', {icon: 1})
            layer.close(index);
        },
        error: function (error) {
            report_success = false
            $("#report_pro_text").append("报告生成失败:" + error)
            layer.alert('报告生失败', {icon: 2})
            layer.close(index);
        }
    })
})

// ---------- 下载报告 ----------
$("#report_download").on("click", function () {
    if (!report_success) {
        layer.alert('请先生成报告', {icon: 3});
        return false;
    }
    // 测试项目
    const selectedValue0 = $('#test_project_type_val').val();
    var filenames = uploadedFileName.join(',');
    window.location.href = '/report_download?test_team=' + selectedValue0 + '&fileName=' + filenames
    uploadedFileName = []
})