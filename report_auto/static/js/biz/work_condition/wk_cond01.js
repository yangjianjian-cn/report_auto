const ignoredKeys = ['timestamps'];
const wk_legend = []
// 使用循环填充 series 数组
const wk_series = [];
// 遍历对象的属性并将它们添加到Map中
Object.keys(work_condition_dict).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        wk_legend.push(key)
        wk_series.push({
            name: key,
            type: 'line',
            data: work_condition_dict[key]
        });
    }
});

const wk01 = echarts.init(document.getElementById('wk_condition_01'), null, {
    renderer: 'canvas',
    useDirtyRect: false
});

const wkOption01 = {
    title: {
        text: 'Work Condition'
    },
    tooltip: {
        trigger: 'axis',
        show: true
    },
    legend: {
        type: 'scroll',
        orient: 'vertical',
        right: 150,
        top: 40,
        bottom: 5,
        show: true,
        width: 100,
        formatter: function (name) {
            return echarts.format.truncateText(name, 100, '14px Microsoft Yahei', '…');
        },
        tooltip: {
            show: true
        },
        data: wk_legend
    },
    grid: {
        left: '10%',
        right: '32%',
        bottom: '3%',
        top: 80,
        containLabel: true
    },
    toolbox: {
        show: true,
        feature: {
            dataZoom: {
                yAxisIndex: "none"
            },
            restore: {}
        }
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: work_condition_dict.timestamps,
        name: 'Time',
        axisLabel: {
            formatter: '{value} s'
        },
        startValue: 0,
        interval: 10
    },
    yAxis: {
        type: 'value',
        name: '',
        axisLabel: {
            formatter: '{value}'
        }
    },
    series: wk_series
};

wk01.setOption(wkOption01);