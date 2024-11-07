let myChart = echarts.init(document.getElementById('temperature_duration'), null, {
    renderer: 'canvas',
    useDirtyRect: false
});

let option = {
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
            text: 'ECU TECU_t  temperature duration',
            subtext: 'Total (minutes) ' + totalMinutes_tecut,
            left: '20%',
            textAlign: 'center'
        },
        {
            text: 'ECU Ambient temperature duration',
            subtext: 'Total (minutes) ' + total_minutes_tc1th9,
            right: '2%',
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
    xAxis: [
        {
            type: 'value',
            max: totalMinutes_tecut,
            splitLine: {
                show: false
            }
        }
    ],
    yAxis: [
        {
            type: 'category',
            data: Object.keys(timeDiffs_tecut),
            axisLabel: {
                interval: 0,
                rotate: 30
            },
            splitLine: {
                show: false
            }
        }
    ],
    series: [
        {
            type: 'bar',
            stack: 'chart',
            z: 3,
            label: {
                position: 'right',
                show: true
            },
            data: Object.keys(timeDiffs_tecut).map(function (key) {
                return timeDiffs_tecut[key];
            })
        },
        {
            type: 'pie',
            radius: [0, '40%'],
            center: ['60%', '50%'],
            emphasis: {
                focus: 'self'
            },
            data: Object.keys(timeDiffs_tecut).map((key) => {
                return {
                    name: key,
                    value: timeDiffs_tecut[key]
                };
            })
        },
        {
            type: 'pie',
            radius: [0, '40%'],
            center: ['85%', '50%'],
            emphasis: {
                focus: 'self'
            },
            data: Object.keys(time_diffs_tc1th9).map((key) => {
                return {
                    name: key,
                    value: time_diffs_tc1th9[key]
                };
            })
        }
    ]
};

myChart.setOption(option);