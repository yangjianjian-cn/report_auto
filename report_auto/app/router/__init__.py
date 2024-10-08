__coding__ = "utf-8"

from flask import Blueprint

report_bp = Blueprint('report', __name__, url_prefix='/report')
temperature_bp = Blueprint('temperature', __name__, url_prefix='/temperature')

import app.router.ReportAuto
import app.router.Temperature