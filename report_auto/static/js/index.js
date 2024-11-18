$("#report_pro_text").on("dblclick", function () {
    $("#report_pro_text").empty()
})

// ---------- 生成报告 ----------
$("#report_generation").on("click", function () {
    let filenames = uploadedFileName.join(',');
    if (filenames == '') {
        layer.alert('Please upload the file first.', {icon: 5});
        return false;
    }

    let j_test_project_type_id = $("#test_project_type_id").val();

    if ("1" == j_test_project_type_id) {
        layer.open({
            type: 2,
            title: 'Hardware, software, and author information',
            shadeClose: false,
            shade: 0,
            anim: 5,
            maxmin: true, //开启最大化最小化按钮
            area: ['893px', '600px'],
            content: '/report/1/mst_header_page',
            success: function (layero, index) {
                console.log(layero);
                console.log(index);
            },
            end: function () {
                back_page();
            }
        });
    } else {
        back_page();
    }

})

// ---------- 下载报告 ----------
$("#report_download").on("click", function () {
    // 测试项目
    const selectedValue0 = $('#test_project_type_val').val();
    const filenames = uploadedFileName.join(',');
    if (filenames != '') {
        window.location.href = '/report/report_download?test_team=' + selectedValue0 + '&fileName=' + filenames
    } else {
        layer.alert('Please upload the measurement file and generate the test report, and then click Download.', {icon: 7})
    }
    uploadedFileName = []
})

// ---------- 提示信息 ----------
$('#APP_PL_BR_1_SPAN').on('mouseenter', function () {
    const that = this;
    layer.tips('Brake Override Accelerator', that, {tips: 1});

});
$('#Brk_04_SPAN').on('mouseenter', function () {
    const that = this;
    layer.tips('Main Brake Plausibility Check (DIO)', that, {tips: 1});

});
$('#Brk_05_SPAN').on('mouseenter', function () {
    const that = this;
    layer.tips('Redundant Brake Plausibility Check (DIO)', that, {tips: 1});

});
$('#NGS_06_SPAN').on('mouseenter', function () {
    const that = this;
    layer.tips('Neutral Gear Sensor Plausibility Check (Digital Sensor)', that, {tips: 1});

});
$('#Clth_05_SPAN').on('mouseenter', function () {
    const that = this;
    layer.tips('Plausibility check of CLTH-stuck (Digital Sensor-Top Clutch)r', that, {tips: 1});

});
$('#Clth_06_SPAN').on('mouseenter', function () {
    const that = this;
    layer.tips('Plausibility check of CLTH-stuck (Digital Sensor-Bottom Clutch)', that, {tips: 1});
});

function back_page() {
    $('#report_generation').prop('disabled', true);

    let selectedValue0 = $('#test_project_type_val').val();

    let selectedValue1 = $('#select1').val();
    if (selectedValue1 == 'undefined' || selectedValue1 == undefined) {
        selectedValue1 = '';
    }

    let selectedValues2 = $('#select2').val();
    let selected2DataLabel = $('#select2').find('option:selected').attr('data-label');
    if (selectedValues2 == 'undefined' || selectedValues2 == undefined) {
        selectedValues2 = ''
    }

    const test_project_type_id = $("#test_project_type_id").val();
    if ('2' == test_project_type_id) {
        if (selectedValue1 == '' || selectedValues2 == '') {
            layer.alert('Please select a test scenario', {icon: 3})
            return false;
        }
    }

    const jsonData = JSON.stringify({
        "test_team": selectedValue0,
        "test_scenario": selectedValue1,
        "test_area": selectedValues2,
        "test_area_dataLabel": selected2DataLabel,
        "u_files": uploadedFileName.join(',')
    });

    const index = layer.load(0, {shade: false}); //0代表加载的风格，支持0-2

    // 生成报告
    $.ajax({
        url: '/report/generate_report',
        type: 'POST',
        dataType: 'json',
        data: jsonData,
        contentType: 'application/json; charset=utf-8',
        success: function (response) {
            $('#report_generation').prop('disabled', false);
            layer.close(index);

            ret_report_success = response.generate_report_success
            if (ret_report_success != undefined && ret_report_success != '') {
                report_success = true
                console.log(ret_report_success)
                $("#report_pro_text").append('<span style="color: black;">' + response.generate_report_success + '</span>')
                layer.alert('Report generated successfully', {icon: 1})
            }

            ret_report_failed = response.generate_report_failed
            if (ret_report_failed != undefined && ret_report_failed != '') {
                report_success = false
                console.log(ret_report_failed)
                $("#report_pro_text").append('<span style="color: indianred;">' + response.generate_report_failed + '</span>')
                layer.alert('Report generated unsuccessfully', {icon: 5})
            }
        },
        error: function (error) {
            report_success = false
            $("#report_pro_text").append("Report generation error:" + error.msg())
            layer.alert('generate_report_error', {icon: 2})
            layer.close(index);
        }
    })
}
