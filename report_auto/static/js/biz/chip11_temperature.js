let myChart11 = echarts.init(document.getElementById('chip_temperature11'), null, {
    renderer: 'canvas',
    useDirtyRect: false
});

let option11 = {
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
            text: 'ECU Internal Ambient temperature(X2)',
            subtext: 'Total (minutes) ' + total_minutes_x2,
            right: '5%',
            textAlign: 'left'
        }
    ],
    grid: [
        {
            top: '15%',
            width: '40%',
            height: '60%',
            right: '1%',
            containLabel: true
        }
    ],
    series: [
        {
            type: 'pie',
            radius: [0, '40%'],
            center: ['52%', '50%'],
            emphasis: {
                focus: 'self'
            },
            label: {
                formatter: '{b}: ({d}%) '
            },
            labelLayout:{
                draggable:true
            },
            data: Object.keys(time_diffs_x2).map((key) => {
                return {
                    name: key,
                    value: time_diffs_x2[key]
                };
            })
        }
    ]
};

myChart11.setOption(option11);