from flask import Blueprint

grievance_bp = Blueprint('grievance', __name__, url_prefix='/grievance')

from . import routes
