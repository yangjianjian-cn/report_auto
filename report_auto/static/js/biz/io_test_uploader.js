(function ($) {
    $(function () {
        let $wrap = $('#uploader'),

            // 图片容器
            $queue = $('<ul class="filelist"></ul>').appendTo($wrap.find('.queueList')),

            // 状态栏，包括进度和控制按钮
            $statusBar = $wrap.find('.statusBar'),

            // 文件总体选择信息。
            $info = $statusBar.find('.info'),

            // 上传按钮
            $upload = $wrap.find('.uploadBtn'),

            // 没选择文件之前的内容。
            $placeHolder = $wrap.find('.placeholder'),

            $progress = $statusBar.find('.progress').hide(),

            // 添加的文件数量
            fileCount = 0,

            // 添加的文件总大小
            fileSize = 0,

            // 优化retina, 在retina下这个值是2
            ratio = window.devicePixelRatio || 1,

            // 缩略图大小
            thumbnailWidth = 110 * ratio,
            thumbnailHeight = 110 * ratio,

            // 可能有pedding, ready, uploading, confirm, done.
            state = 'pedding',

            // 所有文件的进度信息，key为file id
            percentages = {},
            // WebUploader实例
            uploader = WebUploader.create({
                pick: {
                    id: '#filePicker',
                    label: '点击选择文件'
                },
                dnd: '#uploader .queueList',
                paste: '#uploader',
                swf: '/static/swf/Uploader.swf',
                chunked: false, //此处禁用了分块
                chunkSize: 512 * 1024,
                server: '/report/iotest/upload',
                accept: {
                    title: 'Measurement files',
                    extensions: 'dat'
                },

                // 禁掉全局的拖拽功能。这样不会出现图片拖进页面的时候，把图片打开。
                disableGlobalDnd: true,
                fileNumLimit: 0,
                fileSizeLimit: 0,    // 200 M = 200 * 1024 * 1024
                fileSingleSizeLimit: 50 * 1024 * 1024,    // 50 M
                directories: true
            });
        // uploader初始化...
        uploader.onReady = function () {
            window.uploader = uploader;
        };
        // 加入Queued队列前
        uploader.onBeforeFileQueued = function (file) {

        };
        // 加入Queued队列
        uploader.onFileQueued = function (file) {
            fileCount++;
            fileSize += file.size;

            if (fileCount === 1) {
                $placeHolder.addClass('element-invisible');
                $statusBar.show();
            }

            addFile(file);
            setState('ready');
            updateTotalProgress();
        };
        // 该批次全部加入Queued队列
        uploader.onFilesQueued = function (file) {
        };
        // 移除Queued队列
        uploader.onFileDequeued = function (file) {
            fileCount--;
            fileSize -= file.size;

            if (!fileCount) {
                setState('pedding');
            }

            removeFile(file);
            updateTotalProgress();
        };

        uploader.on('dndAccept', function (items) {
            const allowedExtensions = ['.dat'];
            const acceptedItems = [];
            const rejectedItems = [];

            items.forEach(item => {
                const fileName = item.name.toLowerCase();
                const extension = fileName.slice(fileName.lastIndexOf('.') || Infinity);

                if (allowedExtensions.includes(extension)) {
                    acceptedItems.push(item);
                } else {
                    rejectedItems.push(item);
                }
            });

            if (rejectedItems.length > 0) {
                //'以下文件因扩展名不正确而被拒绝:', rejectedItems.map(item => item.name));
                layer.alert(`有 ${rejectedItems.length} 个文件未被接受，请确保只拖放 .dat 文件。`, {icon: 3});
            }

            return acceptedItems.length === items.length;
        });
        uploader.on('dialogOpen', function () {
        });

        // 添加“添加文件”的按钮，
        //uploader.addButton({
            //id: '#filePicker2',
            //label: '&nbsp;&nbsp;&nbsp;&nbsp;Keep adding&nbsp;&nbsp;&nbsp;&nbsp;'
       // });

        // 当有文件添加进来时执行，负责view的创建
        function addFile(file) {
            var $li = $('<li id="' + file.id + '">' +
                    '<p class="title">' + file.name + '</p>' +
                    '<p class="imgWrap"></p>' +
                    '<p class="progress"><span></span></p>' +
                    '</li>'),

                $btns = $('<div class="file-panel">' +
                    '<span class="cancel">删除</span>' +
                    '<span class="rotateRight">向右旋转</span>' +
                    '<span class="rotateLeft">向左旋转</span></div>').appendTo($li),
                $prgress = $li.find('p.progress span'),
                $wrap = $li.find('p.imgWrap'),
                $info = $('<p class="error"></p>'),

                showError = function (code) {
                    switch (code) {
                        case 'exceed_size':
                            text = '文件大小超出';
                            layer.alert(text, {icon: 3});
                            break;

                        case 'interrupt':
                            text = '上传暂停';
                            layer.alert(text, {icon: 3});
                            break;

                        default:
                            text = '上传失败，请重试';
                            layer.alert(text, {icon: 3});
                            break;
                    }

                    $info.text(text).appendTo($li);
                };

            if (file.getStatus() === 'invalid') {
                showError(file.statusText);
            } else {
                $wrap.text('预览中');
                uploader.makeThumb(file, function (error, src) {
                    var img;
                    img = $('<img src="' + src + '">');
                    $wrap.empty().append(img);

                    if (error) {
                        let relativePath_yl = file.source?.source?.webkitRelativePath ?? file.source?.webkitRelativePath ?? '';
                        // 假设路径分隔符是斜杠 '/'
                        const separator = '/';

                        // 分割路径为各部分，并过滤掉空的部分
                        const pathParts = relativePath_yl.split(separator).filter(part => part.length > 0);

                        // 检查是否以文件扩展名结尾
                        const hasExtension = /\.[^/.]+$/.test(pathParts[pathParts.length - 1]);

                        // 计算目录层数，不包括文件名
                        const directoryLevels = pathParts.length - (hasExtension ? 1 : 0);

                        // 如果目录层数大于3，则从右往左取第3层目录名称
                        let thirdFromRight;
                        if (directoryLevels > 3) {
                            thirdFromRight = pathParts[pathParts.length - 3];
                        } else {
                            thirdFromRight = '路径层数不大于3';
                        }

                        $wrap.text(thirdFromRight);
                        return;
                    }
                }, thumbnailWidth, thumbnailHeight);

                percentages[file.id] = [file.size, 0];
                file.rotation = 0;
            }

            file.on('statuschange', function (cur, prev) {
                if (prev === 'progress') {
                    $prgress.hide().width(0);
                } else if (prev === 'queued') {
                    $li.off('mouseenter mouseleave');
                    $btns.remove();
                }
                // 成功
                if (cur === 'error' || cur === 'invalid') {
                    showError(file.statusText);
                    percentages[file.id][1] = 1;
                } else if (cur === 'interrupt') {
                    showError('interrupt');
                } else if (cur === 'queued') {
                    $info.remove();
                    $prgress.css('display', 'block');
                    percentages[file.id][1] = 0;
                } else if (cur === 'progress') {
                    $info.remove();
                    $prgress.css('display', 'block');
                } else if (cur === 'complete') {
                    $prgress.hide().width(0);
                    $li.append('<span class="success"></span>');
                }

                $li.removeClass('state-' + prev).addClass('state-' + cur);
            });

            $li.on('mouseenter', function () {
                $btns.stop().animate({height: 30});
            });

            $li.on('mouseleave', function () {
                $btns.stop().animate({height: 0});
            });

            $btns.on('click', 'span', function () {
                let index = $(this).index(),
                    deg;

                switch (index) {
                    case 0:
                        uploader.removeFile(file);
                        return;

                    case 1:
                        file.rotation += 90;
                        break;

                    case 2:
                        file.rotation -= 90;
                        break;
                }
            });

            $li.appendTo($queue);
        }

        // 负责view的销毁
        function removeFile(file) {
            const $li = $('#' + file.id);

            delete percentages[file.id];
            updateTotalProgress();
            $li.off().find('.file-panel').off().end().remove();
        }

        function updateTotalProgress() {
            let loaded = 0,
                total = 0,
                spans = $progress.children(),
                percent;

            $.each(percentages, function (k, v) {
                total += v[0];
                loaded += v[0] * v[1];
            });

            percent = total ? loaded / total : 0;


            spans.eq(0).text(Math.round(percent * 100) + '%');
            spans.eq(1).css('width', Math.round(percent * 100) + '%');
            updateStatus();
        }

        function updateStatus() {
            let text = '', stats;

            if (state === 'ready') {
                text = '选中' + fileCount + '个文件，共' + WebUploader.formatSize(fileSize) + '。';
            } else if (state === 'confirm') {
                stats = uploader.getStats();
                if (stats.uploadFailNum) {
                    text = '已成功上传' + stats.successNum + '个文件，' +
                        stats.uploadFailNum + '个文件上传失败，<a class="retry" href="#">重新上传</a>失败文件或<a class="ignore" href="#">忽略</a>'
                }

            } else {
                stats = uploader.getStats();
                text = '共' + fileCount + '个（' +
                    WebUploader.formatSize(fileSize) +
                    '），已上传' + stats.successNum + '个';

                if (stats.uploadFailNum) {
                    text += '，失败' + stats.uploadFailNum + '个';
                }
            }

            $info.html(text);
        }

        function setState(val) {
            let file, stats;

            if (val === state) {
                return;
            }

            $upload.removeClass('state-' + state);
            $upload.addClass('state-' + val);
            state = val;

            switch (state) {
                case 'pedding':
                    $placeHolder.removeClass('element-invisible');
                    $queue.hide();
                    $statusBar.addClass('element-invisible');
                    uploader.refresh();
                    break;

                case 'ready':
                    $placeHolder.addClass('element-invisible');
                    $('#filePicker2').removeClass('element-invisible');
                    $queue.show();
                    $statusBar.removeClass('element-invisible');
                    uploader.refresh();
                    break;

                case 'uploading':
                    $('#filePicker2').addClass('element-invisible');
                    $progress.show();
                    $upload.text('暂停上传');
                    break;

                case 'paused':
                    $progress.show();
                    $upload.text('继续上传');
                    break;

                case 'confirm':
                    $progress.hide();
                    $('#filePicker2').removeClass('element-invisible');
                    $upload.text('  Start uploading   ');

                    stats = uploader.getStats();
                    if (stats.successNum && !stats.uploadFailNum) {
                        setState('finish');
                        return;
                    }
                    break;
                case 'finish':
                    stats = uploader.getStats();
                    if (stats.successNum) {
                        //alert('上传成功');
                    } else {
                        // 没有成功的图片，重设
                        state = 'done';
                        location.reload();
                    }
                    break;
            }

            updateStatus();
        }

        // 文件开始上传
        uploader.onUploadStart = function (file) {
        };
        // 文件上传请求发送之前
        uploader.on('uploadBeforeSend', function (object, data, headers) {
            // 获取文件对象和自定义数据
            let file = object.file;

            // 直接从 file.source 中获取 relativePath
            let relativePath = file.source?.source?.webkitRelativePath ?? file.source?.webkitRelativePath ?? '';

            // 获取测试团队信息
            let test_team = $('#select0').val();

            // 将相对路径和测试团队信息添加到请求的 formData 中
            data.test_team = test_team;
            data.relativePath = relativePath;
        });

        uploader.onUploadSuccess = function (file, response) {
            uploadedFileName.push(file.name);
        };

        uploader.on('all', function (type) {
            switch (type) {
                case 'uploadFinished':
                    // 所有文件上传完成
                    setState('confirm');
                    break;

                case 'uploadAccept':
                    // 文件上传请求被服务器接受
                    break;

                case 'startUpload':
                    // 手动启动文件上传
                    setState('uploading');
                    break;

                case 'stopUpload':
                    setState('paused');
                    break;

            }
        });

        uploader.onError = function (code) {
            let text = code;
            switch (code) {
                case "F_DUPLICATE":
                    text = "重复上传"
                    layer.alert(text, {icon: 0});
                    break;
                case "Q_EXCEED_NUM_LIMIT":
                    text = "超过允许上传的文件个数"
                    layer.alert(text, {icon: 0});
                    break;
                default:
                    console.log('Error: ' + text)
            }
        };
        $upload.on('click', function () {
            if ($(this).hasClass('disabled')) {
                return false;
            }
            if (state === 'ready') {
                uploader.upload();
            } else if (state === 'paused') {
                uploader.upload();
            } else if (state === 'uploading') {
                uploader.stop();
            }
        });

        $info.on('click', '.retry', function () {
            uploader.retry();
        });

        $info.on('click', '.ignore', function () {
            console.log('todo');
        });

        $upload.addClass('state-' + state);
        updateTotalProgress();

        $('#select0').on('change', function () {
            fileCount = 0;
            fileSize = 0;
            $queue.hide();
            $placeHolder.removeClass('element-invisible');
            $statusBar.addClass('element-invisible');

            if (!fileCount) {
                setState('pedding');
            }
            updateTotalProgress();

            const $filelist = $('.filelist');
            $filelist.empty();
        });
    });

})(jQuery);


document.getElementById('filePicker').addEventListener('change', function (event) {
    const files = event.target.files;
    // 清空之前的文件列表
    uploader.reset();

    for (let i = 0; i < files.length; i++) {
        let file = files[i];
        let relativePath = file.webkitRelativePath;
        // 将相对路径和其他自定义数据作为自定义属性传递给 WebUploader
        uploader.addFile(file, {relativePath: relativePath});
    }
});

// 文件选择器的 change 事件
document.getElementById('customFilePicker').addEventListener('click', function () {
    let select0_val = $('#select0').val();
    if (select0_val == '') {
        layer.alert('Please select project', {icon: 3})
        return false;
    }
    document.getElementById('filePicker').click();
});
