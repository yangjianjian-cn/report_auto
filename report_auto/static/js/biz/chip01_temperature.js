var temperature_time_dc1_legend = document.getElementById('temperature_time_dc1_legend').value;
temperature_time_dc1_legend = temperature_time_dc1_legend.replace(/'/g, '"'); // 将所有单引号替换为双引号
temperature_time_dc1_legend = JSON.parse(temperature_time_dc1_legend); // 使用JSON.parse将字符串转换为数组
temperature_time_dc1_legend.pop()

var temperatureTime1 = document.getElementById('temperature_time_dc1').value;
temperatureTime1 = temperatureTime1.replace(/'/g, '"'); // 将所有单引号替换为双引号
temperatureTime1 = JSON.parse(temperatureTime1); // 使用JSON.parse将字符串转换为数组
temperatureTime1.pop()

var dom1 = document.getElementById('chip_temperature01');
var chipChart01 = echarts.init(dom1, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

var chipOption01;

chipOption01 = {
    title: {
        text: 'Correlation between chips and TECU_T',
        subtext: 'DC1_Th'
    },
    tooltip:c_tooltip,
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
        data: temperature_time_dc1_legend
    },
    grid:c_grid,
    xAxis: c_xAxis,
    yAxis: c_yAxis,
    series: temperatureTime1
};

if (chipOption01 && typeof chipOption01 === 'object') {
    chipChart01.setOption(chipOption01);
}