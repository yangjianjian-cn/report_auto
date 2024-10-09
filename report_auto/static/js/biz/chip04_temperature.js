var dom4 = document.getElementById('chip_temperature04');
var chipChart04 = echarts.init(dom4, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

// 配置项
var chipOption04 = {
    title: {
        text: '示例图表'
    },
    tooltip: {
        trigger: 'axis'
    },
    legend: {
        type: 'scroll',
        orient: 'vertical',
        left: 'right',
        top: 30,
        bottom: 5,
        tooltip: {
            show: true
        },
        data: ['线条A线条A线条A线条A线条A线条A线条A线条A线条A线条A1111111111111111111111111111111111', '线条B'] // 添加第二个图例项
    },
    xAxis: {
        type: 'value',
        boundaryGap: [0, '100%']
    },
    yAxis: {
        type: 'value',
        scale: true,
        splitNumber: 5,
        axisLabel: {
            formatter: '{value}'
        }
    },
    series: [
        // 第一个系列，线条A
        {
            name: '线条A线条A线条A线条A线条A线条A线条A线条A线条A线条A1111111111111111111111111111111111',
            type: 'line',
            data: [
                {name: '点1', value: [80, 10]},
                {name: '点2', value: [90, 20]},
                {name: '点3', value: [70, 30]},
                {name: '点4', value: [100, 40]},
            ]
        },
        // 第二个系列，线条B
        {
            name: '线条B',
            type: 'line',
            data: [
                {name: '点1', value: [70, 15]},
                {name: '点2', value: [80, 25]},
                {name: '点3', value: [90, 35]},
                {name: '点4', value: [60, 45]},
            ],
            markPoint: {
                data: [
                    {type: 'max', name: '最大值'},
                    {type: 'min', name: '最小值'}
                ]
            },
            markLine: {
                data: [
                    {type: 'average', name: '平均值'}
                ]
            }
        }
    ]
};
// 使用刚指定的配置项和数据显示图表。
chipChart04.setOption(chipOption04);