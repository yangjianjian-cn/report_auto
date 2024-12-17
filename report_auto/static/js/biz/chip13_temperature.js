const temperatureTime13 = temperature_line_dict;

const ignoredKeys = ['timestamps'];
const legend13 = []
// 使用循环填充 series 数组
const series13 = [];
// 遍历对象的属性并将它们添加到Map中
Object.keys(temperatureTime13).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        legend13.push(key)
        if (j_work_condition_label.includes(key)) {
            series13.push({
                name: key,
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: temperatureTime13[key]
            });
        } else {
            series13.push({
                name: key,
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: temperatureTime13[key]
            });
        }

    }
});

const chipChart13 = echarts.init(document.getElementById('chip_temperature13'), null, {
    renderer: 'canvas',
    useDirtyRect: true
});

const chipOption13 = {
    title: {
        text: 'Temperature Time Curve'
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
        data: legend13
    },
    grid: [
        {
            left: '10%',
            right: '32%',
            height: '35%',
            containLabel: true
        },
        {
            left: '10%',
            right: '32%',
            height: '35%',
            top: '58%',
            containLabel: true
        }
    ],
    axisPointer: {
        link: [
            {
                xAxisIndex: 'all'
            }
        ]
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
    dataZoom: [
        // {
        //     show: true,
        //     realtime: true,
        //     start: 10,
        //     end: 70,
        //     xAxisIndex: [0, 1]
        // },
        {
            type: 'inside',
            realtime: true,
            start: 10,
            end: 70,
            xAxisIndex: [0, 1]
        }
    ],
    xAxis: [
        {
            gridIndex: 0,
            type: 'category',
            boundaryGap: false,
            name: 'Time',
            axisLabel: {
                formatter: '{value} s'
            },
            axisLine: {onZero: true},
            data: temperatureTime13.timestamps,
        },
        {
            gridIndex: 1,
            type: 'category',
            boundaryGap: false,
            name: '',
            axisLabel: {
                formatter: '{value} s'
            },
            axisLine: {onZero: true},
            data: temperatureTime13.timestamps,
            position: 'bottom'
        }
    ],
    yAxis: [
        {
            gridIndex: 0,
            type: 'value',
            name: 'Temperature',
            axisLabel: {
                formatter: '{value}°C'
            }
        },
        {
            gridIndex: 1,
            type: 'value',
            name: 'Work Condition',
            axisLabel: {
                formatter: '{value}'
            },
            inverse: true,
            position: 'bottom',
            nameLocation: 'start'
        },
    ],
    series: series13
};

chipChart13.setOption(chipOption13);
