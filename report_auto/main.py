from app import main
from app.router import report_bp, temperature_bp

main.register_blueprint(report_bp, url_prefix='/report')
main.register_blueprint(temperature_bp, url_prefix='/temperature')


# 启动事件
@main.before_request
def startup_event():
    print("Starting up...")
    # 初始化代码，例如连接数据库等


# 关闭事件
@main.teardown_appcontext
def shutdown_event(exception=None):
    print("Shutting down...")
    # 清理代码，例如关闭数据库连接等


if __name__ == '__main__':
    main.run(debug=True, threaded=True)
