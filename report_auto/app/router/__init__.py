__coding__ = "utf-8"

from flask import Blueprint

report_bp = Blueprint('report', __name__, url_prefix='/report')
import app.router.ReportAuto

temperature_bp = Blueprint('temperature', __name__, url_prefix='/temperature')
import app.router.Temperature
import app.router.TemperatureUpload
import app.router.TemperatureAnalysis
import app.router.TemperatureOverview
import app.router.TemperatureDetail