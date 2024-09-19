console.log(counters)
var dom = document.getElementById('chart1');
var charts1 = echarts.init(dom, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var option1 = {
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

if (option1 && typeof option1 === 'object') {
    charts1.setOption(option1);
}

// 初始化第二个饼图
var chart2 = echarts.init(document.getElementById('chart2'));
var option2 = {
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
                {value: counters.app_pl_br_1, name: 'APP_PL_BR_1'},
                {value: counters.brk_04, name: 'Brk_04'},
                {value: counters.brk_05, name: 'Brk_05'},
                {value: counters.ngs_06, name: 'NGS_06'},
                {value: counters.clth_05, name: 'Clth_05'},
                {value: counters.clth_06, name: 'Clth_06'},

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
chart2.setOption(option2);

// 初始化第三个饼图
var chart3 = echarts.init(document.getElementById('chart3'));
var option3 = {
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