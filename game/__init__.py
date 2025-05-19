from flask import Blueprint

game_bp = Blueprint('game', __name__,
                   template_folder='templates',
                   static_folder='static',
                   static_url_path='/game/static')

import game.routes
