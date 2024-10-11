let dom9 = document.getElementById('chip_temperature09');
let chipChart09 = echarts.init(dom9, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

let chipOption09 = {
    title: {
        text: 'Temperature threshold and relative temperature difference',
        subtext: 'Relative temperature difference = (chip temperature threshold, minus the maximum measurement temperature of the chip) divided by the chip temperature threshold'
    },
    tooltip: {
        trigger: 'axis'
    },
    toolbox: {
        show: true,
        feature: {
            restore: {},
            saveAsImage: {}
        }
    },
    grid: {
        top: 90,
        bottom: 70
    },
    dataZoom: [
        {
            type: 'inside'
        },
        {
            type: 'slider'
        }
    ],
    xAxis: {
        type: 'category',
        name: 'Chip Name',
        axisPointer: {
            type: 'shadow'
        },
        data: chipNames
    },
    yAxis: {
        name: 'Temperature',
        type: 'value'
    },
    series: [
        // 温度阈值 - 折线图
        {
            name: 'max allowed temperature',
            type: 'line',
            data: maxAllowedValues,
            tooltip: {
                valueFormatter: function (value) {
                    return value + ' °C';
                }
            },
            label: {
                show: true,
                position: 'top',
                formatter: '{c}'
            },
            emphasis: {
                focus: 'series'
            }
        },
        // 最大温度 - 柱形图
        {
            name: 'max measurement temperature',
            type: 'bar',
            showBackground: true,
            data: max_temperature,
            label: {
                show: true,
                position: 'top',
                formatter: '{c}'
            },
            tooltip: {
                valueFormatter: function (value) {
                    return value + ' °C';
                }
            },
            emphasis: {
                focus: 'series'
            },
            stack: 'st'
        },
        // 相对温差 = (温度阈值 - 最大温度) / 温度阈值
        {
            name: 'relative difference temperature',
            type: 'bar',
            showBackground: true,
            data: relative_difference_temperature,
            label: {
                show: false,
                position: 'bottom',
                formatter: '{c}'
            },
            tooltip: {
                show: true,
                valueFormatter: function (value) {
                    return -value + ' %';
                }
            },
            emphasis: {
                focus: 'series'
            },
            stack: 'st'
        }
    ]
};

// 使用刚指定的配置项和数据显示图表。
chipChart09.setOption(chipOption09);