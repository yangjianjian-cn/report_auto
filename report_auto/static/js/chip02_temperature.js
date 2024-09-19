var dom = document.getElementById('chip_temperature02');

var temperature_timeJson2 = document.getElementById('temperature_time_tc1').value;
var temperatureTime2 = JSON.parse(temperature_timeJson2);

// 使用循环填充 series 数组
var series2 = [];
legend02 = []

// 遍历对象的属性并将它们添加到Map中
Object.keys(temperatureTime2).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        legend02.push(key)
        series2.push({
            name: key,
            type: 'line',
            stack: 'Total',
            data: temperatureTime2[key]
        });
    }
});

var dom = document.getElementById('chip_temperature02');
var chipChart02 = echarts.init(dom, null, {
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
        show:true
    },
    legend: {
        type: 'scroll',
        orient: 'vertical',
        left: 450,
        top: 10,
        data: legend02
    },
    grid: {
        left: '10%',
        right: '32%',
        bottom: '3%',
        top: 80,
        containLabel: true
    },
    toolbox: {
        // feature: {
        //     saveAsImage: {}
        // }
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: temperatureTime2.timestamps
    },
    yAxis: {
        type: 'value'
    },
    series: series2
};

if (chipOption02 && typeof chipOption02 === 'object') {
    chipChart02.setOption(chipOption02);
}

// window.addEventListener('resize', chipChart.resize);