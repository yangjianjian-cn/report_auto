// 获取 total_minutes 的值
var totalMinutes = document.getElementById('total-minutes').value;

// 获取 time_diffs 的值，并解析为 JSON 对象
var timeDiffsJson = document.getElementById('time-diffs').value;
var timeDiffs = JSON.parse( timeDiffsJson);

var dom = document.getElementById('temperature_duration');
var myChart = echarts.init(dom, null, {
    renderer: 'canvas',
    useDirtyRect: false
});
var app = {};

var option;

const builderJson = {
    charts: timeDiffs
};
const downloadJson = timeDiffs;

// const waterMarkText = 'RBCD-EED';
// const canvas = document.createElement('canvas');
// const ctx = canvas.getContext('2d');
// canvas.width =200;
// ctx.textAlign = 'center';
// ctx.textBaseline = 'middle';
// ctx.globalAlpha = 0.08;
// ctx.font = '20px Microsoft Yahei';
// ctx.translate(50, 50);
// ctx.rotate(-Math.PI / 4);
// ctx.fillText(waterMarkText, 0, 0);

option = {
    // backgroundColor: {
    //     type: 'pattern',
    //     image: canvas,
    //     repeat: 'repeat'
    // },
    tooltip: {},
    title: [
        {
            text: 'TECU_T temperature duration',
            subtext: 'Total (minutes) ' + totalMinutes,
            left: '25%',
            textAlign: 'center'
        },
        {
            text: 'TECU_T temperature duration',
            subtext:
                'Total (minutes)' + totalMinutes,
            left: '75%',
            textAlign: 'center'
        }
    ],
    grid: [
        {
            top: 50,
            width: '40%',
            height: '60%',
            bottom: '45%',
            left: 10,
            containLabel: true
        },
        {
            top: 50,
            width: '50%',
            height: '60%',
            bottom: 0,
            left: 10,
            containLabel: true
        }
    ],
    xAxis: [
        {
            type: 'value',
            max: totalMinutes,
            splitLine: {
                show: false
            }
        }
    ],
    yAxis: [
        {
            type: 'category',
            data: Object.keys(builderJson.charts),
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
            data: Object.keys(builderJson.charts).map(function (key) {
                return builderJson.charts[key];
            })
        },
        {
            type: 'bar',
            stack: 'chart',
            silent: true,
            itemStyle: {
                color: '#eee'
            },
            data: Object.keys(builderJson.charts).map(function (key) {
                return builderJson.all - builderJson.charts[key];
            })
        },
        {
            type: 'pie',
            radius: [0, '40%'],
            center: ['75%', '40%'],
            data: Object.keys(downloadJson).map(function (key) {
                return {
                    name: key.replace('.js', ''),
                    value: downloadJson[key]
                };
            })
        }
    ]
};

if (option && typeof option === 'object') {
    myChart.setOption(option);
}
// window.addEventListener('resize', myChart.resize);