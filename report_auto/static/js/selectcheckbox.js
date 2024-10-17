function updateSelectCheck2() {
    var select1 = document.getElementById("select1");
    var select2 = document.getElementById("select2");

    // 清空select2
    while (select2.firstChild) {
        select2.removeChild(select2.firstChild);
    }

    if (select1.value === "analogue_input") {
        var options = ['I_A_APP1', 'I_A_APP2', 'I_A_BPS', 'I_A_BTS', 'I_A_CTS', 'I_A_OPS', 'I_A_OTS', 'I_A_RAILPS', 'I_A_RmtAPP1', 'I_A_RmtAPP2', 'I_A_TL'];
        options.forEach(function (optionValue) {
            var option = document.createElement("option");
            option.value = optionValue;
            option.textContent = optionValue;
            select2.appendChild(option);
        });
    } else if (select1.value === "digital_input") {
        var options = ['I_S_VSLIM', 'I_S_T15', 'I_S_T50', 'I_S_WFLS'];
        options.forEach(function (optionValue) {
            var option = document.createElement("option");
            option.value = optionValue;
            option.textContent = optionValue;
            select2.appendChild(option);
        });
    }
}
