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
            subtext: 'Total (minutes) ' + total_minutes_tecut,
            left: '50%',
            textAlign: 'center',
            align: 'center'
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
            max: total_minutes_tecut,
            splitLine: {
                show: false
            }
        }
    ],
    yAxis: [
        {
            type: 'category',
            data: Object.keys(time_diffs_tecut),
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
            data: Object.keys(time_diffs_tecut).map(function (key) {
                return time_diffs_tecut[key];
            })
        },
        {
            type: 'pie',
            radius: [0, '40%'],
            center: ['75%', '50%'],
            emphasis: {
                focus: 'self'
            },
            selectedMode: 'single',
            label: {
                formatter: '{b}: ({d}%) '
            },
            labelLayout: {
                draggable: true
            },
            data: Object.keys(time_diffs_tecut).map((key) => {
                return {
                    name: key,
                    value: time_diffs_tecut[key]
                };
            })
        }
    ]
};

myChart.setOption(option);