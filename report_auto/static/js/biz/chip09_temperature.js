let dom9 = document.getElementById('chip_temperature09');
let chipChart09 = echarts.init(dom9, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

let chipOption09 = {
    title: {
        text: '温度阈值和相对温差',
        subtext: '相对温差= (芯片温度阈值 减 芯片最大测量温度) 除以 芯片温度阈值'
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
        // 折线图
        {
            name: 'max allowed temperature',
            type: 'line',
            data: maxAllowedValues,
            tooltip: {
                valueFormatter: function (value) {
                    return value + ' °C';
                }
            }
        },
        // 柱形图
        {
            name: 'relative difference',
            type: 'bar',
            data: differenceTemperatures,
            label: {
                show: true,
                position: 'top',
                formatter: '{c}'
            },
            tooltip: {
                valueFormatter: function (value) {
                    return value + ' %';
                }
            }
        }
    ],
    // 添加阴影区域
    graphic: [
        {
            type: 'rect',
            left: 'center',
            top: '10%', // 调整阴影区域的起始位置
            z: -1,
            shape: {
                width: '90%',
                height: '10%' // 调整阴影区域的高度
            },
            style: {
                fill: 'rgba(0, 0, 0, 0.1)' // 设置阴影颜色和透明度
            }
        }
    ]
};

// 使用刚指定的配置项和数据显示图表。
chipChart09.setOption(chipOption09);