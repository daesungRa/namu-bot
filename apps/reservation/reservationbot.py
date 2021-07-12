import logging
from typing import Union, Dict, List, Tuple, Optional

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

    def _make_contents(self, command: str, *args):
        """
        Take action and Return response_title, response_body by reservation step.
        If there is nothing to respond to, it can return a Tuple object filled with None.
        The action is started with command described below,

        :param command:
            '/start ': First step of reservation flow. In this case, previous session is initialized.
            '/disconnect ': Stop the reservation flow. In this case, connected chat's redis session is deleted.
        :param args:
            Additional values for each step.

        :return title:
            Title of response text, string type.
        :return body:
            Body of response text, string type.
        """
        title, body = None, None

        if command == '/start':
            self._delete_session()
            self._touch_or_create_session()
            title, body = f'Hi, {self.username}', "This is first step of reservation flow."
        elif command == '/disconnect':
            self._delete_session()
            title = f'Bye, {self.username}'

        return title, body

    def action_by_step(self) -> Union[Dict, List]:
        """Take action and Return send_result."""
        if self.bot_status == 2:  # Status of bot_command
            command, *args = self.text.split(' ')
            title, body = self._make_contents(command, *args)
            self.set_response(resp_title=title, resp_body=body)

        send_result = self.send_response()
        return {'ok': send_result}
