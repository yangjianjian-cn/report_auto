let work_condition_file = new Set();
let j_work_condition_file = $('init_selected_files').val()
if (typeof j_work_condition_file != "undefined") {
    let filesArray = j_work_condition_file.split(',');
    filesArray.forEach(function (fileId) {
        fileId = fileId || ''; // 如果 fileId 为 null 或 undefined，则赋值为空字符串
        fileId = fileId.trim(); // 去掉前后空白字符

        if (fileId) { // 检查 fileId 是否非空
            work_condition_file.add(fileId);
        }
    });
}


$('#example-multiple-optgroups').multiselect({
    enableClickableOptGroups: false,
    enableCollapsibleOptGroups: true,
    disableIfEmpty: true,
    maxHeight: 200,
    inheritClass: true,
    numberDisplayed: 3,
    delimiterText: '; ',
    widthSynchronizationMode: 'ifPopupIsSmaller',
    onChange: function (option, checked) {
        let current_selected_file_name = $(option).val()
        if (checked) {
            work_condition_file.add(current_selected_file_name)
        } else {
            work_condition_file.delete(current_selected_file_name)
        }
    },
    onDropdownHidden: function (event) {
        if (work_condition_file.size > 0) {
            layer.load(0, {shade: false});
            let selectedFilesString = Array.from(work_condition_file).join(',');
            let encodedSelectedFiles = encodeURIComponent(selectedFilesString);
            window.location.href = '/temperature/working_condition?fileId=' + encodedSelectedFiles;
        }
    }
});