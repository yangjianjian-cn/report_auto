var temperature_time_tc1_legend = document.getElementById('temperature_time_tc1_legend').value;
temperature_time_tc1_legend = temperature_time_tc1_legend.replace(/'/g, '"'); // 将所有单引号替换为双引号
temperature_time_tc1_legend = JSON.parse(temperature_time_tc1_legend); // 使用JSON.parse将字符串转换为数组
temperature_time_tc1_legend.pop()

var temperatureTime2 = document.getElementById('temperature_time_tc1').value;
temperatureTime2 = temperatureTime2.replace(/'/g, '"'); // 将所有单引号替换为双引号
temperatureTime2 = JSON.parse(temperatureTime2); // 使用JSON.parse将字符串转换为数组
temperatureTime2.pop()

var dom2 = document.getElementById('chip_temperature02');
var chipChart02 = echarts.init(dom2, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption02;

chipOption02 = {
    title: {
        subtext: 'TC1_Th'
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
        data: temperature_time_tc1_legend
    },
    grid: c_grid,
    xAxis: c_xAxis,
    yAxis: c_yAxis,
    series: temperatureTime2
};

if (chipOption02 && typeof chipOption02 === 'object') {
    chipChart02.setOption(chipOption02);
}