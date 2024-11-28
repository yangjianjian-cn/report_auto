const temperature_time_dc1_legend = temperature_legend_list; // 使用JSON.parse将字符串转换为数组

let temperatureTime1 = temperature_scatter_list;

const chipChart12 = echarts.init(document.getElementById('chip_temperature12'), null, {
    renderer: 'canvas',
    useDirtyRect: false
});

let chipOption12 = {
    title: {
        text: 'Correlation between chips and ' + j_measurement_source_text
    },
    tooltip: c_tooltip,
    toolbox: c_toolbox,
    brush: {},
    legend: {
        type: 'scroll',
        orient: 'vertical',
        right: 150,
        top: 40,
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
    grid: c_grid,
    xAxis: c_xAxis,
    yAxis: c_yAxis,
    series: temperatureTime1
};
chipChart12.setOption(chipOption12);
