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

![io](https://github.com/user-attachments/assets/ce3fb364-f95d-479c-a398-32c441d0f142)



2. **生成Excel(xlsm)报告**

*访问：http://127.0.0.1:5000/report/2*
![image-20241212152330891](https://github.com/user-attachments/assets/14cf627d-edcd-47c2-95bd-81783ce1e6bf)



3. **数据可视化**

​	*访问:http://127.0.0.1:5000/temperature/list*

![image-20241212152623404](https://github.com/user-attachments/assets/1017e8eb-3ad0-4c94-9009-989948f4f0a1)


## 代码结构

以下是 Report Auto 项目的详细目录结构及各部分的功能说明：本工具为基于Python语言的Flask Web应用程序，采用MySQL存储数据
![image](https://github.com/user-attachments/assets/cb833898-588e-4e23-8297-098e327ca974)


### 关键模块说明
![image](https://github.com/user-attachments/assets/f8cb05ec-330e-4805-b916-b3c60b89934a)


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

![image](https://github.com/user-attachments/assets/e982143e-e863-471e-96bf-b62459dec857)


app/__init__.py，一个读取report_auto/.env文件，加载环境变量到系统的程序

 

3.  定义路由，注册蓝图

![image](https://github.com/user-attachments/assets/4c68b66c-50ac-4092-aba1-954f9de2aa53)

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

![image](https://github.com/user-attachments/assets/243c5b4c-3049-410d-88ee-f2f2e022dfc8)


路由处理函数对参数进行校验、转换后，调用service模块，编写业务逻辑



5. 数据访问层及各种工具类

![image](https://github.com/user-attachments/assets/61a7a13c-5de6-471a-8163-448976045cfa)

tools/utils/**.py

service模块编写业务逻辑，会存储、检索、修改、删除数据，DBOperator.py定义了一些方法，对MySQL中的数据，进行增删改查操作，此外还有其它的一些工具类、例如：MySQL连接池管理ConnectionUtils.py、相同前缀的文件名的文件合并CsvFileCombineUtil.py、日期格式转换DateUtils.py、doc合并和文件路径处理类FileUtils.py、动态生成html类HtmlGenerator.py、excel文件处理类xlsm_utils.py、数学运算处理类MathUtils.py等等

6.  自动化报告模块
![image](https://github.com/user-attachments/assets/30bd9e5a-483d-470a-be7f-6cf308147f78)


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
