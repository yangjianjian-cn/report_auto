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
        trigger: 'axis',
        axisPointer: {
            type: 'cross',
            crossStyle: {
                color: '#999'
            }
        }
    },
    toolbox: {
        show: true,
        feature: {
            restore: {}
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
            name: 'max_temperature',
            type: 'bar',
            showBackground: false,
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
        // 温度阈值 - 最大温度
        {
            name: 'difference temperature',
            type: 'bar',
            showBackground: false,
            data: difference_temperature,
            label: {
                show: false,
                position: 'top',
                formatter: '{c}'
            },
            tooltip: {
                show: false, // 不显示这个系列的提示
                valueFormatter: function (value) {
                    return value + ' °C';
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