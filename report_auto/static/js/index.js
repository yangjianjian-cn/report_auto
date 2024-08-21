$("#report_pro_text").on("dblclick", function () {
    $("#report_pro_text").empty()
})
$("#report_generation").on("click", function () {
    $('#report_generation').prop('disabled', true);

    $.ajax({
        url: '/generate_report',
        type: 'POST',
        dataType: 'json',
        success: function (response) {
            $("#report_pro_text").append("报告生成成功:" + response.generate_report_success + "\r\n")
            $('#report_generation').prop('disabled', false);
        },
        error: function (error) {
            $("#report_pro_text").append("报告生成失败:" + error)
        }
    })
})

$("#report_download").on("click", function () {
    window.location.href = '/report_download'
    $("#report_pro_text").append("\r\n已下载...")
})