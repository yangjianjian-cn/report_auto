// 初始化图表实例
let dom = document.getElementById('chip_temperature10');
let myChart = echarts.init(dom, null, {
    renderer: 'canvas',
    useDirtyRect: false
});

// 指定图表的配置项和数据
var option = {
    title: {
        text: '学生最喜欢的水果',
        subtext: '数据来自班级调查',
        x: 'center'
    },
    legend: {
        orient: 'vertical',
        left: 'left',
        data: ['苹果', '香蕉', '橙子', '葡萄']
    },
    series: [
        {
            name: '水果偏好',
            type: 'pie',
            radius: '55%',
            center: ['50%', '60%'],
            data: [
                [1, '苹果', 15],
                [2, '香蕉', 10],
                [3, '橙子', 20],
                [4, '葡萄', 5]
            ],
            label: {
                show: true, // 显示标签
                position: 'outside', // 标签的位置，可以是 'inside' 或 'outside'
                formatter: function (params) {
                    // 计算百分比
                    const total = option.series[0].data.reduce((sum, item) => sum + item[2], 0);
                    const percentage = ((params.value[2] / total) * 100).toFixed(2);
                    return `${params.value[1]}\n${percentage}%`;
                }
            }
        }
    ]
};

// 添加 visualMap 配置
option.visualMap = {
    type: 'continuous',
    show: true, // 显示视觉映射条
    min: 1, // 最小值应与数据中的最小 index 匹配
    max: 4, // 最大值应与数据中的最大 index 匹配
    orient: 'vertical',
    dimension: 0, // 修改为 0，指向 index 字段
    inRange: {
        color: ['#0000FF', '#00FF00', '#FFFF00', '#FF0000'] // 定义颜色范围
    }
};

// 使用刚指定的配置项和数据显示图表。
myChart.setOption(option);