var temperature_timeJson7 = document.getElementById('temperature_time_tc2_7').value;
var temperatureTime7 = JSON.parse(temperature_timeJson7);


// 使用循环填充 series 数组
var series7 = [];
legend07 = []

// 遍历对象的属性并将它们添加到Map中
Object.keys(temperatureTime7).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        legend07.push(key)
        series7.push({
            name: key,
            type: 'line',
            stack: 'Total',
            data: temperatureTime7[key]
        });
    }
});

var dom7 = document.getElementById('chip_temperature07');
var chipChart07 = echarts.init(dom7, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption07 = {
    title: {
        subtext: 'TC2_Th'
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
        data: legend07
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
        data: temperatureTime7.timestamps,
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
    series: series7
};

if (chipOption07 && typeof chipOption07 === 'object') {
    chipChart07.setOption(chipOption07);
}

// window.addEventListener('resize', chipChart.resize);