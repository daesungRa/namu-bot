"""
Account api module.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
from flask import render_template, make_response, redirect

from apps.flasklib import ApiBlueprint


LOGGER = logging.getLogger(__name__)
API = ApiBlueprint(__name__, url_prefix='/account')


@API.route('/login')
def login():
    """
    TODO: Apply login system.
        Show login page if not logged in.
        Redirect to main page if logged in.
    """
    # TODO: Login action.
    # TODO: Set user's cookie to response.
    return render_template('login.html')


@API.route('/logout')
def logout():
    """
    TODO: Go to main page after logged out.
    """
    # TODO: Logout action.
    # TODO: Update login status.
    response = make_response(redirect('/'))
    # TODO: Handling cookie. This case, delete user's cookie from response object.
    return response
