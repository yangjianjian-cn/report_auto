const temperature_time_legend_new = [];
if (temperature_legend_list.length > 0) {
    for (let i = 0; i <= temperature_legend_list.length - 1; i++) {
        if (!j_work_condition_label.includes(temperature_legend_list[i])) {
            temperature_time_legend_new.push(temperature_legend_list[i]);
        }
    }
}

c_tooltip = {
    showDelay: 0,
    formatter: function (params) {
        if (params.value.length > 1) {
            return (
                params.seriesName +
                ' :<br/>' +
                params.value[0] +
                '°C ' +
                params.value[1] +
                '°C '
            );
        } else {
            return (
                params.seriesName +
                ' :<br/>' +
                params.name +
                ' : ' +
                params.value +
                '°C '
            );
        }
    },
    axisPointer: {
        show: true,
        type: 'cross',
        lineStyle: {
            type: 'dashed',
            width: 1
        }
    }
}
c_toolbox = {
    feature: {
        dataZoom: {}
        ,
        brush: {
            type: ['rect', 'polygon', 'clear']
        }
        ,
        restore: {}
    }
}
c_grid = {
    left: '10%',
    right: '32%',
    bottom: '3%',
    top: 80,
    containLabel: true
}
c_xAxis = {
    type: 'value',
    scale: true,
    name: j_measurement_source_text,
    axisLabel: {
        formatter: '{value}°C'
    },
    splitLine: {
        show: false
    }
}
c_yAxis = {
    type: 'value',
    scale: true,
    splitNumber: 5,
    name: 'Temperature',
    formatter: function (value) {
        return value.toFixed(1) + '°C';
    }
}

const chipChart12 = echarts.init(document.getElementById('chip_temperature12'), null, {
    renderer: 'canvas',
    useDirtyRect: true
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
        data: temperature_time_legend_new
    },
    grid: c_grid,
    xAxis: c_xAxis,
    yAxis: c_yAxis,
    series: temperature_scatter_list
};
chipChart12.setOption(chipOption12);
