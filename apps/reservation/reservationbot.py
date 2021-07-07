import logging
from typing import Union, Dict, List

from apps.telegrambot import TelegramBot
from config import CONFIG


LOGGER = logging.getLogger(__name__)

_RESERV_CONF = CONFIG['APPS']['reservation']
_RESERV_WEBHOOK_DOMAIN = f'{_RESERV_CONF["telegram.webhook.SEND_URL"]}{_RESERV_CONF["telegram.bot.API_TOKEN"]}'


class ReservationBot(TelegramBot):
    def __init__(self, telegram_info: Dict):
        """Set webhook domain for reservation."""
        self.webhook_domain = _RESERV_WEBHOOK_DOMAIN

        super().__init__(telegram_info=telegram_info)

    def _make_contents(self, command: str, data: List):
        """
        self.text startswith:
            '/login ':
            '/area ':
            '/date ':
            '/time ':
        :return:
            title: str, body: str
            None, None
        """
        if command == '/start':
            return None, "Please insert ID and PWD.\nInsert format is '/login [ID] [PWD]'"
        elif command == '/login':
            login_id, login_pw = data[0], data[1]
            result = True
            return f"[LOGIN] {'성공' if len(data) == 2 and result else '실패'}", f'ID: {login_id}, PW: {login_pw}'
        return None, None

    def action_by_step(self) -> Union[Dict, List]:
        action_result = {}
        title, body = None, None
        if self.bot_status == 2:
            command, *data = self.text.split(' ')
            title, body = self._make_contents(command, data)

        self._set_response(resp_title=title, resp_body=body)
        if self.bot_status >= 2:
            self._send_response()
        else:
            LOGGER.warning(f'[SEND-ACTION] bot_status: {self.bot_status}')
        return action_result
