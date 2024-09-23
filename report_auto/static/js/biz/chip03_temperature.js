var temperature_time_tc2_legend = document.getElementById('temperature_time_tc2_legend').value;
temperature_time_tc2_legend = temperature_time_tc2_legend.replace(/'/g, '"'); // 将所有单引号替换为双引号
temperature_time_tc2_legend = JSON.parse(temperature_time_tc2_legend); // 使用JSON.parse将字符串转换为数组
temperature_time_tc2_legend.pop()

var temperatureTime3 = document.getElementById('temperature_time_tc2').value;
temperatureTime3 = temperatureTime3.replace(/'/g, '"'); // 将所有单引号替换为双引号
temperatureTime3 = JSON.parse(temperatureTime3); // 使用JSON.parse将字符串转换为数组
temperatureTime3.pop()

var dom3 = document.getElementById('chip_temperature03');
var chipChart03 = echarts.init(dom3, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption03;

chipOption03 = {
    title: {
        text: 'TC2_Th'
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
        data: temperature_time_tc2_legend
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
            magicType: {
                type: ["line", "bar"]
            },
            restore: {},
            saveAsImage: {}
        }
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        name: 'TECU_T',
        axisLabel: {
            formatter: '{value}°C'
        }
    },
    yAxis: {
        type: 'value',
        scale: true,
        splitNumber: 5,
        name: '温度',
        axisLabel: {
            formatter: '{value}°C'
        }
    },
    series: temperatureTime3
};

if (chipOption03 && typeof chipOption03 === 'object') {
    chipChart03.setOption(chipOption03);
}

// window.addEventListener('resize', chipChart.resize);