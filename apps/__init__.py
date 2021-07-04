"""
Flask web application for facility-reserv.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

from gevent import monkey
monkey.patch_all()

import os
import logging
import requests

from pathlib import Path
from logging import Formatter
from logging.handlers import TimedRotatingFileHandler
from flask import Flask
from flask_cors import CORS

from apps.flasklib import NamuFlask
from apps.account.api.root import API as ROOT_API
from apps.reservation.api.reservation import API as RESERV_API
from config import CONFIG


LOGGER = logging.getLogger(__name__)

RESERV_CONF = CONFIG['APPS']['reservation']
RESERV_WEBHOOK_DOMAIN = f'{RESERV_CONF["telegram.webhook.SEND_URL"]}{RESERV_CONF["telegram.bot.API_TOKEN"]}'
RESERV_WEBHOOK_STATUS = RESERV_CONF['telegram.webhook.STATUS']
RESERV_RECEIVE_URL = RESERV_CONF['telegram.webhook.RECEIVE_URL']


def create_app() -> Flask:
    app = NamuFlask(__name__)

    set_logger()
    register_blueprints(app)
    set_webhooks()
    app.config['MAX_CONTENT_LENGTH'] = 1 << 40
    app.config['SECRET_KEY'] = os.urandom(12)
    # app.config['PERMANENT_SESSION_LIFETIME'] = config.session_config['permanent_session_lifetime']
    
    CORS(app)

    LOGGER.info('Application setting done..')
    return app


def set_logger():
    fmt = Formatter(
        '[%(levelname)s %(asctime)s %(filename)s:%(lineno)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    root_logger = logging.getLogger()
    for handle in root_logger.handlers:
        root_logger.removeHandler(handle)

    # Add stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(logging.INFO)
    root_logger.addHandler(stream_handler)

    # Add timed file handler
    project_root = Path(__file__).resolve().parent.parent
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / 'app.log',
        when='midnight',
        interval=1,
        backupCount=100,
        encoding='UTF-8',
    )
    file_handler.suffix = '%Y-%m-%d'
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)


def register_blueprints(app: Flask):
    app.register_blueprint(ROOT_API)
    app.register_blueprint(RESERV_API)


def set_webhooks():
    """Set or Delete webhook connection with telegram bot."""
    if RESERV_WEBHOOK_STATUS:
        set_reserv_webhook_url = f'{RESERV_WEBHOOK_DOMAIN}/setWebhook?' \
                                 f'url={RESERV_RECEIVE_URL}&drop_pending_updates=true'
        LOGGER.info(requests.get(set_reserv_webhook_url).json()["description"])
    else:
        delete_reserv_webhook_url = f'{RESERV_WEBHOOK_DOMAIN}/deleteWebhook?drop_pending_updates=true'
        LOGGER.info(requests.get(delete_reserv_webhook_url).json()["description"])
