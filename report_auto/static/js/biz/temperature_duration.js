// 获取 total_minutes 的值
let totalMinutes = document.getElementById('total-minutes').value;
let measurement_source =  document.getElementById('measurement_source').value;
debugger
let title_text = 'TECU_T'
if ( 'NG_FILES' == measurement_source){
    title_text = 'NGECU'
}

// 获取 time_diffs 的值，并解析为 JSON 对象
//  [{'40 ~ 45': 0.77, 'idx': 0}, {'45 ~ 50': 62.38, 'idx': 1}, {'50 ~ 55': 5.5600000000000005, 'idx': 2}, {'55 ~ 60': 4.24, 'idx': 3}, {'60 ~ 65': 22.67, 'idx': 4}, {'65 ~ 70': 11.52, 'idx': 5}]
let timeDiffsJson = document.getElementById('time-diffs').value;
let timeDiffs = JSON.parse(timeDiffsJson);

// 定义颜色数组
const t_colors = ['#0000FF', '#00FF00', '#FFFF00', '#FF0000'];

// 使用 reduce 方法转换数据(柱形图)
// {
//     "40 ~ 45": 0.77,
//     "45 ~ 50": 62.38,
//     "50 ~ 55": 5.5600000000000005,
//     "55 ~ 60": 4.24,
//     "60 ~ 65": 22.67,
//     "65 ~ 70": 11.52
// }
const convertedData = timeDiffs.reduce((acc, curr) => {
    // 遍历当前对象的每个属性
    for (let key in curr) {
        if (curr.hasOwnProperty(key) && key !== 'idx') {
            acc[key] = curr[key];
        }
    }
    return acc;
}, {});

// 找到 idx 的最小值和最大值
const idxValues = timeDiffs.map(item => item.idx);
const minIdx = Math.min(...idxValues);
const maxIdx = Math.max(...idxValues);

let dom = document.getElementById('temperature_duration');
let myChart = echarts.init(dom, null, {
    renderer: 'canvas',
    useDirtyRect: false
});
let option;

option = {
    tooltip: {},
    toolbox: {
        show: true,
        feature: {
            saveAsImage: {}
        }
    },
    title: [
        {
            text: title_text +' temperature duration',
            subtext: 'Total (minutes) ' + totalMinutes,
            left: '25%',
            textAlign: 'center'
        },
        {
            text: title_text + ' temperature duration',
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
            data: Object.keys(convertedData),
            axisLabel: {
                interval: 0,
                rotate: 30
            },
            splitLine: {
                show: false
            }
        }
    ],
    // visualMap: {
    //     show: true,
    //     top: 50,
    //     right: 10,
    //     min: minIdx, // 最小idx
    //     max: maxIdx, // 最大idx
    //     inRange: {
    //         color: t_colors // 蓝色到红色渐变
    //     }
    // },
    series: [
        {
            type: 'bar',
            stack: 'chart',
            z: 3,
            label: {
                position: 'right',
                show: true
            },
            data: Object.keys(convertedData).map(function (key) {
                return convertedData[key];
            })
        },
        {
            type: 'pie',
            radius: [0, '40%'],
            center: ['75%', '40%'],
            emphasis: {
                focus: 'self'
            },
            data: Object.keys(convertedData).map((key, index) => {
                const idx = timeDiffs.find(item => Object.keys(item).includes(key)).idx;
                console.log(idx)
                return {
                    name: key,
                    value: convertedData[key]
                };
            })
        }
    ]
};
if (option && typeof option === 'object') {
    myChart.setOption(option);
}