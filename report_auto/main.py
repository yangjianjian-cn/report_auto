from flask import Flask

from app.router import report_bp, temperature_bp

main = Flask(__name__, template_folder='templates', static_folder='static')
main.register_blueprint(report_bp, url_prefix='/report')
main.register_blueprint(temperature_bp, url_prefix='/temperature')

if __name__ == '__main__':
    main.run(debug=True, threaded=True)
