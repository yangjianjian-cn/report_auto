var temperature_timeJson5 = document.getElementById('temperature_time_dc1_5').value;
var temperatureTime5 = JSON.parse(temperature_timeJson5);

const ignoredKeys = ['timestamps'];
legend05 = []
// 使用循环填充 series 数组
var series5 = [];
// 遍历对象的属性并将它们添加到Map中
Object.keys(temperatureTime5).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        legend05.push(key)
        series5.push({
            name: key,
            type: 'line',
            stack: 'Total',
            data: temperatureTime5[key]
        });
    }
});

var dom5 = document.getElementById('chip_temperature05');
var chipChart05 = echarts.init(dom5, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption05;

chipOption05 = {
    title: {
        text: 'Temperature Time Curve',
        subtext: 'DC1_Th'
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
        data: legend05
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
        data: temperatureTime5.timestamps,
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
    series: series5
};

if (chipOption05 && typeof chipOption05 === 'object') {
    chipChart05.setOption(chipOption05);
}

// window.addEventListener('resize', chipChart.resize);