"""
Facility yeyak api version 1.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
from flask import request, jsonify, current_app

from apps.flasklib import ApiBlueprint, ApiView
from apps.exception import DetailedNotFoundError
from apps.reservation.reservationbot import ReservationBot
from config import CONFIG


LOGGER = logging.getLogger(__name__)
API = ApiBlueprint(__name__, url_prefix='/reservation')

RESERV_CONF = CONFIG['APPS']['reservation']
RESERV_WEBHOOK_DOMAIN = f'{RESERV_CONF["telegram.webhook.SEND_URL"]}{RESERV_CONF["telegram.bot.API_TOKEN"]}'


class ReservationApiNotFoundError(DetailedNotFoundError):
    resource_name = 'Reservation Api'


@API.api_view_class
class Reservation(ApiView):
    rules = {
        '': ['POST'],
    }

    def post(self):
        """Receive webhook message from reservation bot."""
        # TODO: Add session flow by chat_id and username(using Redis).
        telegram_info = request.get_json()

        @current_app.after_this_response
        def post_process():
            # this will occur after you finish processing the route & return (below):
            bot = ReservationBot(telegram_info=telegram_info)
            bot.action_by_step()

        return jsonify(data={})
