EXE程序，在电脑上双击，可直接运行。在选择输出目录之前，需要在输出目录放置一些  测试报告模板文件。

例如：输出目录为：D:\report_auto，那么该目录下也要放置 测试报告模板文件



最后运行页面，单击“生成报告”按钮，需要等一会儿，页面上出现“已生成..."的信息，表示 测试报告已经生成



dat_csv.exe文件邮件发不过去，放在了GitHub，路径：https://github.com/yangjj2020/report_auto/tree/master/report_auto/tools/dat/dist

测试报告模板文件位置： https://github.com/yangjj2020/report_auto/tree/master/template


Linux主机部署report_auto, 采用了源码部署方式



① 创建虚拟环境：conda create --name report Python=3.9


② 激活虚拟环境: conda activate report 



③ 创建输出目录：例如 /home/aillm/report_auto/output，output子目录下，放置 测试报告模板
测试报告模板下载路径：https://github.com/yangjj2020/report_auto/tree/master/template


④创建文件上传目录： /home/aillm/report_auto/input ( 在网页上选择的本机dat文件，会上传到服务器该目录 )



⑤ 修改项目report_auto中的配置文件：

https://github.com/yangjj2020/report_auto/blob/master/report_auto/.env

input_path， dat文件存储目录，需要手工创建

output_path， 输出目录，需要手工创建

docx_path， 生成的测试报告,位于输出目录docx子目录，不需要创建，程序自动生成

zip_path， 生成的zip文件，位于输出目录zip子目录，不需要创建，程序自动生成

template_path，测试报告模板文件，位于输出目录template子目录，需要手工上传 测试报告模板文件


⑥ 创建任一目录，用于放置report_auto项目
例如：创建/home/aillm/report_auto/code目录，下载 report_auto项目到/home/aillm/report_auto/code
report_auto项目下载地址： https://github.com/yangjj2020/report_auto/tree/master/report_auto

⑦ 安装依赖包：
进入report_auto项目根目录，执行命令pip install -r requirements.txt ， 安装项目需要的依赖包


⑧ 运行
项目根目录执行命令：nohup gunicorn --bind 0.0.0.0:5000 main:main > gunicorn_output.log 2>&1 &

⑨ 浏览器访问：http://117.50.172.154:5000/
安装依赖包 和 运行 ，这两步可能会遇到问题，到时再一起解决

