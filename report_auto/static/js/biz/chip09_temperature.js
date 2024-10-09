var dom9 = document.getElementById('chip_temperature09');
var chipChart09 = echarts.init(dom9, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption09 = {
    grid: {
        top: '10%',
        height: '80%'
    },
    xAxis: {
        type: 'category',
        data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    },
    yAxis: {
        type: 'value'
    },
    series: [
        // 折线图
        {
            name: 'Line Chart',
            type: 'line',
            data: [120, 200, 250, 380, 470, 510, 130]
        },
        // 柱形图
        {
            name: 'Bar Chart',
            type: 'bar',
            data: [100, 150, 200, 250, 300, 150, 90],
            label: {
                show: true,
                position: 'top',
                formatter: '{c}'
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