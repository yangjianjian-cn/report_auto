let myChart10 = echarts.init(document.getElementById('chip_temperature10'), null, {
    renderer: 'canvas',
    useDirtyRect: false
});

let option10 = {
    tooltip: {},
    toolbox: {
        show: true,
        feature: {
            saveAsImage: {}
        },
        right: '0%',
        top: 1
    },
    title: [
        {
            text: 'ECU Ambient temperature(X3)',
            subtext: 'Total (minutes) ' + total_minutes_x3,
            left: '2%',
            textAlign: 'left'
        }
    ],
    grid: [
        {
            top: '15%',
            width: '40%',
            height: '60%',
            left: '1%',
            containLabel: true
        }
    ],
    series: [
        {
            type: 'pie',
            radius: [0, '40%'],
            center: ['30%', '50%'],
            emphasis: {
                focus: 'self'
            },
            label: {
                formatter: '{b}: ({d}%) '
            },
            labelLayout:{
                draggable:true
            },
            data: Object.keys(time_diffs_x3).map((key) => {
                return {
                    name: key,
                    value: time_diffs_x3[key]
                };
            })
        }
    ]
};

myChart10.setOption(option10);