import logging
import requests
from abc import ABCMeta, abstractmethod
from typing import Union, Optional, Dict, List

from apps.reservation.db.redis.chat_session import ChatSession


LOGGER = logging.getLogger(__name__)


class TelegramBot(metaclass=ABCMeta):
    update_id: Optional[str] = None
    chat_id: Optional[str] = None
    username: Optional[str] = None
    chat_session: Optional[ChatSession] = None
    text: Optional[str] = None
    response_title: Optional[str] = None
    response_body: Optional[str] = None
    bot_status: int = 0  # 0: build, 1: error, 2: bot_command, 3: message
    webhook_domain: Optional[str] = None

    def __init__(self, telegram_info: Dict):
        """
        Create a TelegramBot instance with the passed telegram_info.
        This contains redis chat_session created by chat_id.

        :param telegram_info.my_chat_member.old_chat_member.status:
            'member': When disconnecting.
            'kicked': Create a new connection, kicked off!
        :param telegram_info.message.entities.$.type:
            'bot_command': Represents a bot command.
        """
        assert telegram_info is not None and 'update_id' in telegram_info

        self.update_id = telegram_info['update_id']
        chat_info = telegram_info['my_chat_member'] if 'my_chat_member' in telegram_info else telegram_info['message']
        self.chat_id = chat_info['chat']['id']
        self.username = f'{chat_info["chat"]["last_name"]}{chat_info["chat"]["first_name"]}'

        # Redis session has values from previous step.
        self._touch_or_create_session()

        if 'my_chat_member' in telegram_info:
            if chat_info['old_chat_member']['status'] == 'kicked':
                LOGGER.info(f'[NEW][{self.chat_id}] Build a new chat with {self.username}')
            else:
                # Disconnect redis session
                self._delete_session()
                LOGGER.info(f'[DISCONNECT][{self.chat_id}] Disconnect with {self.username}')
        elif 'message' in telegram_info:
            self.bot_status = 3  # Status of message
            self.text = chat_info['text']
            if 'entities' in chat_info and chat_info['entities'] and chat_info['entities'][0]['type'] == 'bot_command':
                self.bot_status = 2  # Status of bot_command
            LOGGER.info(f'< [{self.chat_id}][{self.username}] {self.text}')

            # Set default response_title
            self.response_title = f'Unknown command, Received text is "{self.text}".'
        else:
            self.bot_status = 1  # Status of error
            LOGGER.error(
                f'[{self.chat_id}][{self.username}] '
                f'Unknown key was passed with telegram_info. > {telegram_info.keys()}'
            )

    def _touch_or_create_session(self):
        """Touch or Create redis session"""
        session = ChatSession(self.chat_id)
        if not session.exists():
            session.username = self.username
            session.commit()
        session.touch()
        self.chat_session = session

    def _update_session(self, **kwargs):
        """Update redis session with new values"""
        if self.chat_session and self.chat_session.exists():
            self.chat_session.commit(**kwargs)
        else:
            LOGGER.warning(f'[REDIS] There is no session of {self.chat_id}, {self.username}')

    def _delete_session(self):
        """Delete redis session if it exists."""
        if self.chat_session and self.chat_session.exists():
            self.chat_session.delete()

    def set_response(self, resp_title: str, resp_body: str = None):
        """Set responses from inserted info."""
        if resp_title is not None:
            self.response_title = resp_title
        self.response_body = resp_body  # It can be None

    def send_response(self) -> bool:
        """Send message to telegram bot."""
        if self.bot_status >= 2:
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
            return bool(send_result['ok'])
        else:
            LOGGER.warning(f'Message not sent. bot_status: {self.bot_status}')
            return False

    @abstractmethod
    def _make_contents(self, command: str, *args): pass

    @abstractmethod
    def action_by_step(self) -> Union[Dict, List]: pass
