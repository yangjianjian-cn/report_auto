from app import main
from app.router import report_bp, temperature_bp

main.register_blueprint(report_bp, url_prefix='/report')
main.register_blueprint(temperature_bp, url_prefix='/temperature')

if __name__ == '__main__':
    main.run(debug=True, threaded=True)
