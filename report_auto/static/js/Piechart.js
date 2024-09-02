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
                {value: 1048, name: 'I/O Test'},
                {value: 735, name: 'MST Test'},
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
                {value: 120, name: 'APP_PL_BR_1'},
                {value: 200, name: 'Brk_04'},
                {value: 154, name: 'Brk_05'},
                {value: 135, name: 'NGS_06'},
                {value: 234, name: 'Clth_05'},
                {value: 234, name: 'Clth_06'},

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
                {value: 1048, name: 'analogue input'},
                {value: 735, name: 'digital input'},
                {value: 580, name: 'PWM input'},
                {value: 484, name: 'digital output'},
                {value: 300, name: 'PWM output'}
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
