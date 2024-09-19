var dom = document.getElementById('chip_temperature03');

var temperature_timeJson3 = document.getElementById('temperature_time_tc2').value;
var temperatureTime3 = JSON.parse(temperature_timeJson3);


// 使用循环填充 series 数组
var series3 = [];
legend03 = []

// 遍历对象的属性并将它们添加到Map中
Object.keys(temperatureTime3).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        legend03.push(key)
        series3.push({
            name: key,
            type: 'line',
            stack: 'Total',
            data: temperatureTime3[key]
        });
    }
});

var dom = document.getElementById('chip_temperature03');
var chipChart03 = echarts.init(dom, null, {
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
        show:true
    },
    legend: {
        type: 'scroll',
        orient: 'vertical',
        left: 450,
        top: 10,
        data: legend03
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
        data: temperatureTime3.timestamps
    },
    yAxis: {
        type: 'value'
    },
    series: series3
};

if (chipOption03 && typeof chipOption03 === 'object') {
    chipChart03.setOption(chipOption03);
}

// window.addEventListener('resize', chipChart.resize);