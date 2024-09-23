var temperature_time_tc1_legend = document.getElementById('temperature_time_tc1_legend').value;
temperature_time_tc1_legend = temperature_time_tc1_legend.replace(/'/g, '"'); // 将所有单引号替换为双引号
temperature_time_tc1_legend = JSON.parse(temperature_time_tc1_legend); // 使用JSON.parse将字符串转换为数组

var temperatureTime2 = document.getElementById('temperature_time_tc1').value;
temperatureTime2 = temperatureTime2.replace(/'/g, '"'); // 将所有单引号替换为双引号
temperatureTime2 = JSON.parse(temperatureTime2); // 使用JSON.parse将字符串转换为数组

var dom2 = document.getElementById('chip_temperature02');
var chipChart02 = echarts.init(dom2, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption02;

chipOption02 = {
    title: {
        text: 'TC1_Th'
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
        data: temperature_time_tc1_legend
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
            dataView: {
                readOnly: false
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
        name: '',
        axisLabel: {
            formatter: '{value}°C'
        }
    },
    series: temperatureTime2
};

if (chipOption02 && typeof chipOption02 === 'object') {
    chipChart02.setOption(chipOption02);
}

// window.addEventListener('resize', chipChart.resize);