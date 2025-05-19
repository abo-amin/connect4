from flask import Blueprint

social_bp = Blueprint('social', __name__, 
                     template_folder='templates',
                     static_folder='static', 
                     url_prefix='/social')

from . import routes
