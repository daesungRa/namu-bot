import logging
import requests
from abc import ABCMeta, abstractmethod
from typing import Union, Optional, Dict, List


LOGGER = logging.getLogger(__name__)


class TelegramBot(metaclass=ABCMeta):
    update_id: Optional[str] = None
    chat_id: Optional[str] = None
    username: Optional[str] = None
    text: Optional[str] = None
    response_title: Optional[str] = None
    response_body: Optional[str] = None
    bot_status: int = 0  # 0: build, 1: error, 2: bot_command, 3: message
    webhook_domain: Optional[str] = None

    def __init__(self, telegram_info: Dict):
        """
        Make a new Telegram bot with the passed telegram_info.

        :param my_chat_member.old_chat_member.status:
            'member': When disconnecting.
            'kicked': Create a new connection, kicked off!
        :param message.entities.$.type:
            'bot_command': Represents a bot command.
        """
        assert telegram_info is not None and 'update_id' in telegram_info

        self.update_id = telegram_info['update_id']
        chat_info = telegram_info['my_chat_member'] if 'my_chat_member' in telegram_info else telegram_info['message']
        self.chat_id = chat_info['chat']['id']
        self.username = f'{chat_info["chat"]["last_name"]}{chat_info["chat"]["first_name"]}'

        if 'my_chat_member' in telegram_info:
            if chat_info['old_chat_member']['status'] == 'kicked':
                LOGGER.info(f'[NEW][{self.chat_id}] Build a new chat with {self.username}')
            else:
                LOGGER.info(f'[DISCONNECT][{self.chat_id}] Disconnect with {self.username}')
        elif 'message' in telegram_info:
            self.bot_status = 3  # message status
            self.text = chat_info['text']
            if 'entities' in chat_info and chat_info['entities'] and chat_info['entities'][0]['type'] == 'bot_command':
                self.bot_status = 2  # bot_command status
            LOGGER.info(f'< [{self.username}] {self.text}')

            # Set default response_title
            self.response_title = f'Unknown command, Received text is "{self.text}".'
        else:
            self.bot_status = 1  # error status

    def _set_response(self, resp_title: str = None, resp_body: str = None):
        """
        Set response_title for init and end.
        extra response_title and response_body will be filled in subclasses.
        """
        if self.bot_status == 2:
            if self.text == '/start':
                self.response_title = f'Hi, {self.username}.'
            elif self.text == '/end':
                self.response_title = f'Bye, {self.username}.'

        if resp_title is not None:
            self.response_title = resp_title
        if resp_body is not None:
            self.response_body = resp_body

    def _send_response(self):
        """Send message to telegram bot."""
        assert self.webhook_domain is not None
        assert self.chat_id is not None
        assert self.response_title is not None

        response = self.response_title
        if self.response_body:
            response = f'{response}\n\n{self.response_body}'
        send_result = requests.post(
            f'{self.webhook_domain}/sendMessage',
            json={
                'chat_id': self.chat_id,
                'text': response,
            }
        ).json()
        LOGGER.info(f"> [{self.username}][{send_result['ok']}] "
                    f"title: {self.response_title}, body: {self.response_body}")

    @abstractmethod
    def _make_contents(self, command: str, data: List): pass

    @abstractmethod
    def action_by_step(self) -> Union[Dict, List]: pass
