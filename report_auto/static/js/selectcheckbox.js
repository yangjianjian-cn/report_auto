function updateSelectCheck2() {
    const select1 = document.getElementById("select1");
    const select2 = document.getElementById("select2");

    // 清空select2
    while (select2.firstChild) {
        select2.removeChild(select2.firstChild);
    }

    const dict_value = select1.value;
    const jsonData = {"dict_value": dict_value}
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
