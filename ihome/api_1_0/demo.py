from . import api
from flask import current_app
from ihome import models


@api.route('/index/')
def index():
    current_app.logger.error('sss')

    return "index"