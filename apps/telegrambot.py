import logging
import requests
from typing import Dict, Optional


LOGGER = logging.getLogger(__name__)


class TelegramBot:
    update_id: Optional[str] = None
    chat_id: Optional[str] = None
    username: Optional[str] = None
    text: Optional[str] = None
    response: Optional[str] = None
    entity_type: Optional[str] = None
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
        self.update_id = telegram_info['update_id']
        chat_info = telegram_info['my_chat_member'] if 'my_chat_member' in telegram_info else telegram_info['message']
        self.chat_id = chat_info['chat']['id']
        self.username = f'{chat_info["chat"]["last_name"]}{chat_info["chat"]["first_name"]}'

        if 'my_chat_member' in telegram_info:
            old_chat_member_status = chat_info['old_chat_member']['status']
            if old_chat_member_status == 'kicked':
                self.response = f'[NEW] {self.username}'
                LOGGER.info(f'[NEW][{self.chat_id}] Build a new chat with {self.username}')
            else:
                self.response = f'[DISCONNECT] {self.username}'
                LOGGER.info(f'[DISCONNECT][{self.chat_id}] Disconnect with {self.username}')
        else:
            self.text = chat_info['text']
            if 'entities' in chat_info and chat_info['entities']:
                self.entity_type = chat_info['entities'][0]['type']
            LOGGER.info(f'< [{self.username}] {self.text}')

    def _set_response(self, resp_type: str):
        if self.entity_type is not None:
            if self.entity_type == 'bot_command':
                if self.text == '/start':
                    self.response = f'Hi, {self.username}.'
                elif self.text == '/end':
                    self.response = f'Bye, {self.username}.'
                else:
                    self.response = f'Unknown command, Received text is "{self.text}".'
            else:
                self.response = f'Empty response, Received text is "{self.text}".'
        else:
            if resp_type == 'repeat':
                self.response = f'{self.text}'

    def send_repeat_message(self):
        self._set_response(resp_type='repeat')
        if self.chat_id and self.text:
            send_result = requests.post(
                f'{self.webhook_domain}/sendMessage',
                json={
                    'chat_id': self.chat_id,
                    'text': self.response,
                }
            ).json()
            LOGGER.info(f"> [{self.username}][{send_result['ok']}] {self.response}")
