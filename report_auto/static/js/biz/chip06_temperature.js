var temperature_timeJson6 = document.getElementById('temperature_time_tc1_6').value;
var temperatureTime6 = JSON.parse(temperature_timeJson6);

// 使用循环填充 series 数组
var series6 = [];
legend06 = []

// 遍历对象的属性并将它们添加到Map中
Object.keys(temperatureTime6).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        legend06.push(key)
        series6.push({
            name: key,
            type: 'line',
            stack: 'Total',
            data: temperatureTime6[key]
        });
    }
});

var dom6 = document.getElementById('chip_temperature06');
var chipChart06 = echarts.init(dom6, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption06 = {
    title: {
        subtext: 'TC1_Th'
    },
    tooltip: {
        trigger: 'axis',
        show: true
    },
    legend: {
        type: 'scroll',
        orient: 'vertical',
        left: 450,
        top: 30,
        bottom: 5,
        show: true,
        width: 100,
        formatter: function (name) {
            return echarts.format.truncateText(name, 100, '14px Microsoft Yahei', '…');
        },
        tooltip: {
            show: true
        },
        data: legend06
    },
    grid: {
        left: '10%',
        right: '32%',
        bottom: '3%',
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
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: temperatureTime6.timestamps,
        name: 'Time',
        axisLabel: {
            formatter: '{value} s'
        }
    },
    yAxis: {
        type: 'value',
        name: 'Temperature',
        axisLabel: {
            formatter: '{value}°C'
        }
    },
    series: series6
};

if (chipOption06 && typeof chipOption06 === 'object') {
    chipChart06.setOption(chipOption06);
}