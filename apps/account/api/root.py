"""
Root api module.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
from flask import request, render_template

from apps.flasklib import ApiBlueprint


LOGGER = logging.getLogger(__name__)
API = ApiBlueprint(__name__, url_prefix='/')


@API.route('')
def root():
    """
    TODO: Apply login system.
        Show login page if not logged in.
    """
    return render_template('index.html')
