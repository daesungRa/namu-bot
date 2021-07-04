import logging
from typing import Dict

from apps.telegrambot import TelegramBot
from config import CONFIG


LOGGER = logging.getLogger(__name__)

_RESERV_CONF = CONFIG['APPS']['reservation']
_RESERV_WEBHOOK_DOMAIN = f'{_RESERV_CONF["telegram.webhook.SEND_URL"]}{_RESERV_CONF["telegram.bot.API_TOKEN"]}'


class ReservationBot(TelegramBot):
    def __init__(self, telegram_info: Dict):
        super().__init__(telegram_info=telegram_info)
        self.webhook_domain = _RESERV_WEBHOOK_DOMAIN

    def _set_response(self, resp_type: str):
        super()._set_response(resp_type=resp_type)
