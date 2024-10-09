let selected_files = new Set();
let j_init_selected_files = $('init_selected_files').val()
if (typeof j_init_selected_files != "undefined") {
    let filesArray = j_init_selected_files.split(',');
    filesArray.forEach(function (fileId) {
        fileId = fileId || ''; // 如果 fileId 为 null 或 undefined，则赋值为空字符串
        fileId = fileId.trim(); // 去掉前后空白字符

        if (fileId) { // 检查 fileId 是否非空
            selected_files.add(fileId);
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
            selected_files.add(current_selected_file_name)
        } else {
            selected_files.delete(current_selected_file_name)
        }
    },
    onDropdownHidden: function (event) {
        if (selected_files.size > 0) {
            layer.load(0, {shade: false});
            let selectedFilesString = Array.from(selected_files).join(',');
            let encodedSelectedFiles = encodeURIComponent(selectedFilesString);
            window.location.href = '/temperature/view?fileId=' + encodedSelectedFiles;
        }
    }
});


