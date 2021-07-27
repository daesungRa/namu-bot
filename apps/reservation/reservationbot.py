import logging
from typing import Union, Dict, List

from apps.telegrambot import TelegramBot
from apps.reservation.yeyak import YeyakHandler

from config import CONFIG


LOGGER = logging.getLogger(__name__)
RESERV_CONF = CONFIG['APPS']['reservation']
RESERV_WEBHOOK_DOMAIN = f'{RESERV_CONF["telegram.webhook.SEND_URL"]}{RESERV_CONF["telegram.bot.API_TOKEN"]}'


class ReservationBot(TelegramBot):
    def __init__(self, telegram_info: Dict):
        """Set webhook domain for reservation."""
        self.webhook_domain = RESERV_WEBHOOK_DOMAIN

        super().__init__(telegram_info=telegram_info)

    def _make_contents(self, command: str, facility_name: str = None, weektime: str = None, *args):
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
        title, body, additional_word = None, None, args[0] if args else None

        if command == '/start':
            self._delete_session()
            self._touch_or_create_session()
            title = f'하이, {self.username}. 축구장을 예약합니다.'
            body = "원하는 [시설명]과 [시간대], [추가검색어]을 입력하세요.\nex) \"/search 보라매 [평일/주말] [추가검색어]\""
        elif command == '/search':
            if facility_name is not None and weektime is not None and weektime in ['평일', '주말']:
                # Send first response
                word = f'"{additional_word}"'
                self.set_response(
                    resp_title=f'"{facility_name}", "{weektime}" {additional_word and word or ""} 검색합니다.',
                    resp_body='100회 탐색 후 종료됩니다.\n결과가 없으면 다시 시도해주세요.',
                )
                self.send_response()

                # Get handler and Open base yeyak url
                yeyak_handler = YeyakHandler()
                yeyak_handler.open()

                # Search activate facility using param
                facilities = yeyak_handler.search_facility(facility_name, weektime)
                if facilities and additional_word:
                    facilities = [f for f in facilities if additional_word in f]
                new_line = '\n'
                body_tail = f'{new_line}{new_line}예약하려면, "/yeyak {facility_name} {weektime} [추가검색어]"'
                self.set_response(
                    resp_title=f'~ 축구장 중간 검색 결과 ~',
                    resp_body=f'{new_line.join(facilities)}{"(결과 없음)" if not facilities else body_tail}',
                )
                self.send_response()

                # Close and Quit browser
                yeyak_handler.quit()

                # Final response
                title, body = f'검색 완료됐습니다!', None
            else:
                title = f'\"/search [시설명] [시간대] [추가검색어]\" 형식으로 입력해주세요.\nex) \"/search 보라매 주말 [추가검색어]\"'
        elif command == '/yeyak':
            if facility_name is not None and weektime is not None and weektime in ['평일', '주말']:
                # Send first response
                word = f'"{additional_word}"'
                self.set_response(
                    resp_title=f'"{facility_name}", "{weektime}" {additional_word and word or ""} 시설을 예약합니다.'
                )
                self.send_response()

                # Get handler and Open base yeyak url
                yeyak_handler = YeyakHandler()
                yeyak_handler.open()

                # Login action, Send message
                yeyak_handler.login()
                self.set_response(resp_title='로그인 성공.')
                self.send_response()

                # Action
                yeyak_handler.yeyak_facility(facility_name, weektime, additional_word)

                # Logout action, Send message
                yeyak_handler.logout()
                self.set_response(resp_title='로그아웃 성공.')
                self.send_response()

                # Close and Quit browser
                yeyak_handler.quit()

                # Final response
                title, body = f'예약 완료됐습니다!', '(예약정보)'
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
