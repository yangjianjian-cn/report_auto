## 简介

`Report Auto` 是一个用于自动化处理和生成报告的Python工具，特别适用于汽车电子系统中的数据分析与报告生成。它能够从`.dat`文件中读取采样数据，执行数据清洗、转换和加载操作，并根据特定的业务需求生成Word（.docx）、Excel（.xlsm）等格式的报告。此外，`Report Auto`支持通过网页界面维护报告模板，并基于这些模板生成最终的报告文件。项目还提供了丰富的数据可视化功能，包括支持标签和维度的定制化展示，帮助用户更好地理解数据。



## 特性

- **多源数据处理：** 直接从.dat文件读取采样数据。

- **数据转换与清洗：** 将原始.dat文件转换为更易于处理的CSV格式，并执行必要的数据清洗操作。

- **灵活的报告生成：**

  支持Word（.docx）和Excel（.xlsm）两种格式的报告。

  模板可以在网页界面上进行维护和管理。

- **强大的数据可视化：**

  绘制离散图查看各电子元器件与特定组件的相关性。

  绘制折线图查看电子元器件温度随时间的变化趋势。

  绘制饼图统计不同温度范围内的时长分布。

  绘制柱形图展示各电子元器件之间的相对温差。

  支持标签和维度的定制化展示，允许用户根据需要选择和配置图表的标签和维度，以获得更加个性化的数据分析视图。

## 安装

### **前置条件**

确保已安装以下软件：

- Python 3.9
- pip
- conda (推荐用于创建隔离环境)

### **安装步骤**

1. **克隆仓库**

   ```shell
   git clone https://github.com/yangjj2020/report_auto.git
   cd report_auto
   ```

   

2. **创建并激活conda环境**	

```shell
conda create --name report python=3.9
conda activate report
```



3. **安装依赖**

​	

```shell
pip install -r requirements.txt
```

4. **安装MySQL(略)**	

5. **启动Web界面**

```shell
nohup gunicorn  -w 3 -b 0.0.0.0:5000 main:main --timeout 300 > gunicorn_output.log 2>&1 & 
```

### **使用方法**

1. **生成word(docx)报告**

*访问：http://127.0.0.1:5000/report/1*

![image-20241212152512672](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20241212152512672.png)

2. **生成Excel(xlsm)报告**

*访问：http://127.0.0.1:5000/report/2*

![image-20241212152330891](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20241212152330891.png)

3. **数据可视化**

​	*访问:http://127.0.0.1:5000/temperature/list*

![image-20241212152623404](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20241212152623404.png)

## 代码结构

以下是 Report Auto 项目的详细目录结构及各部分的功能说明：本工具为基于Python语言的Flask Web应用程序，采用MySQL存储数据

report_auto/
├── app/                    # 应用程序的核心逻辑
│   ├── __init__.py
│   └── ...                 # 其他应用相关模块
├── constant/               # 项目中使用的常量定义
├── pojo/                   # Python对象模型（Plain Old Python Objects），用于表示数据结构
├── static/                 # 静态资源文件
│   ├── css/                # CSS样式文件
│   ├── images/             # 图像文件
│   ├── js/                 # JavaScript脚本文件
│   ├── layer/              # Layer插件相关文件（用于前端弹层）
│   └── swf/                # Flash动画文件（项目未使用）
├── templates/              # 报告生成所用的模板文件（如HTML、Jinja2模板）
├── test/                   # 测试代码
├── tools/                  # 工具库，包含各种辅助功能
│   ├── common/             # 通用工具函数
│   ├── conversion/         # 数据转换工具
│   │   ├── iotest/         # I/O测试相关的转换工具
│   │   └── msttest/        # MST测试相关的转换工具
│   ├── parser/             # 数据解析器
│   ├── report/             # 报告生成工具
│   ├── temperature/        # 温度数据分析工具
│   └── utils/              # 其他实用工具
├── .env                    # 环境变量配置文件
├── main.py                 # 项目入口文件，包含CLI命令解析逻辑
├── report_auto.sh          # Shell脚本，可能用于部署或批处理任务
└── requirements.txt        # 项目依赖列表

### 关键模块说明

**app/**: 包含应用程序的主要逻辑，包括数据处理流程、报告生成等核心功能。
**constant/:** 存储项目中使用的所有常量，如故障类型、测试场景类型、程序中特定业务参数
**pojo/**: 定义了简单的Python类，用于表示数据实体或业务对象。
**static/**: 存放静态资源文件，如CSS、JavaScript、图像等，主要用于前端页面
**templates/**: 存储HTML模板文件，基于Jinja2模板引擎进行渲染
**test/**: 包含单元测试和集成测试代码，确保项目功能的正确性。
**tools/:** 提供了一系列辅助工具，用于支持数据转换、解析、报告生成、温度分析等功能。
**common/**: 通用工具函数，如日期处理、字符串操作等。
**conversion/:** 数据转换工具，特别是针对不同类型的测试数据（如IO测试、MST测试）。
**parser/**: 数据解析器，负责从不同的数据源（如CSV、数据库）读取和解析数据。
**report/**: 报告生成工具，负责根据模板生成最终的报告文件。
**utils/**: 其他实用工具，如日志记录、文件操作等。
**.env**: 环境变量配置文件，用于设置项目运行所需的环境变量。
**main.py**: 项目的入口文件，包含了命令行接口（CLI）的实现，允许用户通过命令行与项目交互。
**report_auto.sh:** 可能是一个Shell脚本，用于简化项目的部署或执行批量任务。
**requirements.txt:** 列出了项目依赖的Python包，方便开发者安装所有必要的库。

### 关键模块详细说明

1. 配置变量

report_auto/.env

```python
input_path=C:\Users\Administrator\Downloads\input
output_path=C:\Users\Administrator\Downloads\output
template_path=C:\Users\Administrator\Downloads
jdbc_mysql=IP:用户:端口:密码:数据库实例
```

一个用于配置环境变量的文件，通常用于存储应用程序所需的设置和敏感信息.

**input_path:**  这个路径指定了dat文件上传后的存储路径

**output_path:** 这个路径指定了Word(docx)、Excel(xlsm)报告的存储路径、一些临时文件也会存储到该目录

**template_path:**  这个路径指定了docx、xlsm模板的存储路径

**jdbc_mysql:**  这个变量配置了MySQL数据库实例的连接参数



2. 加载变量

report_auto/
├── app/                    # 应用程序的核心逻辑
│   ├── __init__.py

app/ __init__.py，一个读取report_auto/.env文件，加载环境变量到系统的程序

 

3.  定义路由，注册蓝图

report_auto/
├── app/                    # 应用程序的核心逻辑

│   ├── router

│   │	── __init__.py

│   │	├── IOTestReport.py

│   │	├── TemperatureUpload.py

...

__init__.py: 这段代码定义了两个蓝图，一个用于报告功能，另一个用于温度相关的功能，每个蓝图都有自己的路由和视图函数，

 IOTestReport.py 和TemperatureUpload.py等等，定义了路由的处理函数，并将路由注册到蓝图。

例如：

ReportAuto.py支持报告生成、报告下载

IOTestReport.py定义了xlsm模板维护功能、

TemperatureConfiguration.py支持维度和指标lable定制化

TemperatureUpload.py支持dat文件上传、和项目信息录入

TemperatureAnalysis.py可查看文件采集列表、实现已采集数据的修改、删除和再分析

TemperatureOverview.py  指标可视化，(数据概览图、以饼图、柱形图形式展示)

TemperatureDetail.py 指标的线性关系、指标时间变化趋势 (数据详情图，以离散图、折线图展示)

...

总之 router模块，接收页面发起的http请求，并从url中获取请求参数包，对参数进行校验、转换



4. 编写业务逻辑

report_auto/
├── app/                    # 应用程序的核心逻辑

│   ├── service

│   │	── iotest

│   │	├── IOTestReportService.py

│   │	├── TemperatureDataService.py

路由处理函数对参数进行校验、转换后，调用service模块，编写业务逻辑



5. 数据访问层及各种工具类

report_auto/
├── tools/                  # 工具库，包含各种辅助功能
│   ├── common/             # 通用工具函数
│   ├── conversion/         # 数据转换工具
│   │   ├── iotest/         # I/O测试相关的转换工具
│   │   └── msttest/        # MST测试相关的转换工具
│   ├── parser/             # 数据解析器
│   ├── report/             # 报告生成工具
│   ├── temperature/        # 温度数据分析工具
│   └── utils/       

tools/utils/**.py

service模块编写业务逻辑，会存储、检索、修改、删除数据，DBOperator.py定义了一些方法，对MySQL中的数据，进行增删改查操作，此外还有其它的一些工具类、例如：MySQL连接池管理ConnectionUtils.py、相同前缀的文件名的文件合并CsvFileCombineUtil.py、日期格式转换DateUtils.py、doc合并和文件路径处理类FileUtils.py、动态生成html类HtmlGenerator.py、excel文件处理类xlsm_utils.py、数学运算处理类MathUtils.py等等

6.  自动化报告模块

report_auto/
├── tools/ 



tools/dat/dat_csv.py 早前编写的基于Ui_Dialog的桌面程序 

dat文件转换成csv文件

tools/parser/dat_csv_doc.py 

tools/common/dat_csv_common.py



分析csv文件

tools/conversion/msttest

tools/conversion/*.py

结合docx模板生成word报告

tools/report/report_generation.py



Excel报告的生成

tools/conversion/iotest/**.py



7. 前端发起请求的几种方式

   ① ajax异步发起

   ```
   $.ajax({
       url: "/temperature/analysis", // 请求地址
       type: "POST", // 请求方法
       data: JSON.stringify(sendData), // 要发送的数据，转换成JSON格式
       contentType: "application/json; charset=utf-8", // 设置请求头，告诉服务器数据格式为JSON
       dataType: "json", // 指定预期服务器返回的数据类型为JSON
       success: function (response) {
           layer.alert("success", {icon: 1});
       },
       error: function (jqXHR, textStatus, errorThrown) {
           layer.alert("Request failed: [", textStatus, "], error details: [", errorThrown + "]", {icon: 2});
       },
       complete: function () {
           layer.close(index);
       }
   });
   ```

   ② fetch异步发起

   ```
   fetch('/temperature/delete_file', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json'
       },
       body: JSON.stringify({id})
   }).then(response => response.json())
       .then(responseData => {
           if (responseData.success) {
               location.reload();
           } else {
               layer.alert('Failed to delete file: ' + responseData.message, {icon: 5});
           }
       })
       .catch(error => {
           layer.alert('An error occurred, please try again: ' + error.message, {icon: 5});
       })
       .finally(() => {
           layer.close(index);
           obj.del();
       });
   ```

8. 程序启动入口

   report_auto/main.py

   创建了一个Flask应用实例，并命名为`main`

   将`report_bp`蓝图注册到`main`应用实例中，并指定了一个URL前缀`/report`，所有`report_bp`蓝图中的路由都会以`/report`开头。

   将`temperature_bp`蓝图注册到`main`应用实例中，并指定了一个URL前缀`/temperature`。所有`temperature_bp`蓝图中的路由都会以`/temperature`开头。

   当访问应用时，可以通过`/report`和`/temperature`这两个URL前缀来访问蓝图中定义的路由和视图。

   

## 贡献

欢迎贡献！请阅读 CONTRIBUTING.md 了解如何为项目做出贡献。以下是几个常见的贡献方式：

- 提交错误报告

- 请求新功能
- 创建拉取请求

## 许可证

本项目遵循 MIT License 许可证。

## 致谢

感谢所有为项目做出贡献的人，以及任何支持项目发展的组织和个人。

## 联系方式

如果你有任何问题或建议，请通过以下方式联系我们：

GitHub Issues: https://github.com/yangjj2020/report_auto/issues
