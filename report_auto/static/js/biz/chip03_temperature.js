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
        subtext: 'TC2_Th'
    },
    tooltip: c_tooltip,
    toolbox: c_toolbox,
    brush: {},
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
        data: temperature_time_tc2_legend
    },
    grid: c_grid,
    xAxis: c_xAxis,
    yAxis: c_yAxis,
    series: temperatureTime3
};

if (chipOption03 && typeof chipOption03 === 'object') {
    chipChart03.setOption(chipOption03);
}