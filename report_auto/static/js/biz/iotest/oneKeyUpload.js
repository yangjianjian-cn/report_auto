// 定义一个处理报告生成或文件验证的通用函数
function handleAction(buttonSelector, url, title, successColor = 'black', errorColor = 'indianred') {
    $(buttonSelector).on("click", function () {
        const button = $(this);
        button.prop('disabled', true);

        // 获取选择的项目值
        const selectedValue0 = $('#select0').val();
        if (!selectedValue0) { // 检查是否选择了项目
            layer.alert('Please select the project.', {icon: 5});
            button.prop('disabled', false); // 如果没有选择项目，重新启用按钮
            return false;
        }

        // 创建JSON数据
        const jsonData = JSON.stringify({"test_team": selectedValue0});

        // 显示加载层
        const index = layer.load(0, {shade: false});

        // 发送AJAX请求
        $.ajax({
            url: url,
            type: 'POST',
            dataType: 'json',
            data: jsonData,
            contentType: 'application/json; charset=utf-8',
            success: function (response) {
                button.prop('disabled', false);
                layer.close(index);

                // 处理响应结果
                handleResponse(response, title, successColor, errorColor);
            },
            error: function (error) {
                const errorMessage = error.responseJSON && error.responseJSON.message || error.statusText;
                $("#report_pro_text").append(`Report generation error: ${errorMessage}<br>`);
                layer.close(index);
                button.prop('disabled', false);
            }
        });
    });
}

// 定义显示结果的函数
function showResults(message, title, color) {
    layer.open({
        type: 1,
        title: title,
        shadeClose: true,
        shade: false,
        maxmin: true, // 开启最大化最小化按钮
        area: ['893px', '600px'],
        content: `<span style="color: ${color};">${message}</span>`
    });
}

// 处理响应结果
function handleResponse(response, title, successColor, errorColor) {
    if (response.generate_report_success.length > 0) {
        showResults(response.generate_report_success, `${title} Success`, successColor);
    }
    if (response.generate_report_failed.length > 0) {
        showResults(response.generate_report_failed, `${title} Failure`, errorColor);
    }
}

// 报告生成按钮事件绑定
handleAction("#iotest_report_generation", '/report/iotest/generate_report', 'IOTest Report Generation');

// 文件验证按钮事件绑定
handleAction("#file_verification", '/report/iotest/verification', 'IOTest File Validation', 'black', 'indianred');

// 清空测试报告
document.getElementById('clean_tplt_file').addEventListener('click', handleClearReportClick);

// 清除测试报告
function handleClearReportClick(event) {
    event.preventDefault();
    let test_file = $("#select0").val();

    // 如果没有选择任何文件，给出提示并返回
    if (!test_file) {
        layer.alert('Please select a test project to clear.', {icon: 3});
        return;
    }

    layer.confirm(`Are you sure you want to clear the test report for ${test_file}?`, {
        title: 'Confirm Clear',
        btn: ['OK', 'Cancel'] // 按钮
    }, function (index) {
        layer.close(index);

        fetch('/report/iotest/clean_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({test_project: test_file})
        })
            .then(response => response.json())
            .then(data => {
                if (data.code === 200) {
                    layer.alert(data.message, {icon: 1}); // 成功信息
                } else {
                    layer.alert(data.message, {icon: 2}); // 错误信息
                }
            })
            .catch(error => {
                layer.alert('An error occurred while trying to clear the test report: ' + error, {icon: 2});
            });
    }, function (index) {
        layer.close(index);
    });
}

$("#iotest_report_download").on("click", function () {
    // 测试项目
    const selectedValue0 = $('#select0').val();
    const encodedValue = encodeURIComponent(selectedValue0);
    window.location.href = '/report/iotest/report_download?test_team=' + encodedValue;
});
