var dom = document.getElementById('chip_temperature01');

var temperature_timeJson1 = document.getElementById('temperature_time_dc1').value;
var temperatureTime1 = JSON.parse(temperature_timeJson1);

const ignoredKeys = ['timestamps'];
legend01 = []
// 使用循环填充 series 数组
var series1 = [];
// 遍历对象的属性并将它们添加到Map中
Object.keys(temperatureTime1).forEach(key => {
    if (!ignoredKeys.includes(key)) {
        legend01.push(key)
        series1.push({
            name: key,
            type: 'line',
            stack: 'Total',
            data: temperatureTime1[key]
        });
    }
});

var chipChart01 = echarts.init(dom, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption01;

chipOption01 = {
    title: {
        text: 'DC1_Th'
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
        data: legend01
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
        data: temperatureTime1.timestamps
    },
    yAxis: {
        type: 'value'
    },
    series: series1
};

if (chipOption01 && typeof chipOption01 === 'object') {
    chipChart01.setOption(chipOption01);
}

// window.addEventListener('resize', chipChart.resize);