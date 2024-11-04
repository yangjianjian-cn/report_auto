let charts1 = echarts.init(document.getElementById('chart1'), null, {
    renderer: 'canvas',
    useDirtyRect: false
});
let option1 = {
    title: {
        subtext: 'test project',
        left: 'center'
    },
    tooltip: {
        trigger: 'item'
    },
    legend: {
        orient: 'vertical',
        left: 'left'
    },
    series: [
        {
            name: 'Test Report',
            type: 'pie',
            radius: ['40%', '70%'],
            data: [
                {value: counters.io_test, name: 'I/O Test'},
                {value: counters.mst_test, name: 'MST Test'},
            ],
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }
    ]
};
charts1.setOption(option1);


// 初始化第三个饼图
let chart3 = echarts.init(document.getElementById('chart3'));
let option3 = {
    title: {
        subtext: 'test scenario',
        left: 'center'
    },
    tooltip: {
        trigger: 'item'
    },
    legend: {
        orient: 'vertical',
        left: 'left'
    },
    series: [
        {
            type: 'pie',
            radius: ['40%', '70%'],
            data: [
                {value: counters.analogue_input, name: 'analogue input'},
                {value: counters.digital_input, name: 'digital input'},
                {value: counters.pwm_input, name: 'PWM input'},
                {value: counters.digital_output, name: 'digital output'},
                {value: counters.pwm_output, name: 'PWM output'}
            ],
            label: {
                show: true,
                position: 'outside'
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }
    ]
};
chart3.setOption(option3);