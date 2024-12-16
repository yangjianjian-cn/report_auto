const temperatureTime13 = temperature_line_dict;
console.log(temperatureTime13)

const ignoredKeys = ['timestamps'];
const legend13 = []
// 使用循环填充 series 数组
const series13 = [];
// 遍历对象的属性并将它们添加到Map中
Object.keys(temperatureTime13).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        legend13.push(key)
        series13.push({
            name: key,
            type: 'line',
            data: temperatureTime13[key]
        });
    }
});

const chipChart13 = echarts.init(document.getElementById('chip_temperature13'), null, {
    renderer: 'canvas',
    useDirtyRect: false
});

const chipOption13 = {
    title: {
        text: 'Temperature Time Curve'
    },
    tooltip: {
        trigger: 'axis',
        show: true
    },
    legend: {
        type: 'scroll',
        orient: 'vertical',
        right: 150,
        top: 40,
        bottom: 5,
        show: true,
        width: 100,
        formatter: function (name) {
            return echarts.format.truncateText(name, 100, '14px Microsoft Yahei', '…');
        },
        tooltip: {
            show: true
        },
        data: legend13
    },
    grid: {
        left: '10%',
        right: '32%',
        bottom: '15%',
        top: 80,
        containLabel: true
    },
    toolbox: {
        show: true,
        feature: {
            dataZoom: {
                yAxisIndex: "none"
            },
            restore: {}
        }
    },
    dataZoom: [
        {
            show: true,
            realtime: true,
            start: 10,
            end: 70,
            xAxisIndex: [0, 1]
        },
        {
            type: 'inside',
            realtime: true,
            start: 10,
            end: 70,
            xAxisIndex: [0, 1]
        }
    ],
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: temperatureTime13.timestamps,
        name: 'Time',
        axisLabel: {
            formatter: '{value} s'
        },
        startValue: 0,
        interval: 10
    },
    yAxis: {
        type: 'value',
        name: 'Temperature',
        axisLabel: {
            formatter: '{value}°C'
        }
    },
    series: series13
};

chipChart13.setOption(chipOption13);
