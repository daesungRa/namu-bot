import logging
from typing import Union, Dict, List, Tuple

from apps.flasklib import deprecated
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

    @deprecated
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
                # Send first message
                word = f'"{additional_word}"'
                self.set_response(
                    resp_title=f'"{facility_name}", "{weektime}" {additional_word and word or ""} 검색합니다.',
                    resp_body='100회 탐색 후 종료됩니다.\n결과가 없으면 다시 시도해주세요.',
                )
                self.send_response()

                # Get handler and Open base yeyak url
                yeyak_handler = YeyakHandler()
                yeyak_handler.open()

                # Search open facilities using param
                facilities = []
                for result in yeyak_handler.search_facility(facility_name, weektime, additional_word):  # Use generator
                    if result and isinstance(result, int):
                        self.set_response(resp_title=f'{result}회 검색')
                        self.send_response()
                    elif result and isinstance(result, list):
                        facilities = result

                # Send message of search result
                new_line = '\n'
                body_tail = f'{new_line}{new_line}예약하려면, "/yeyak {facility_name} {weektime} [추가검색어]"'\
                    if len(facilities) > 1 else ''
                self.set_response(
                    resp_title=f'~ 축구장 검색 결과 ~',
                    resp_body=f'{new_line.join([f[1] for f in facilities])}'
                              f'{"(결과 없음)" if not facilities else body_tail}',
                )
                self.send_response()

                # Activate yeyak there is only one result
                if len(facilities) == 1:
                    self.set_response(
                        resp_title=f'"{facilities[0][1]}" 예약을 시작합니다.',
                    )
                    self.send_response()

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

                # Final message
                title, body = f'완료됐습니다!', None
            else:
                title = f'\"/search [시설명] [시간대] [추가검색어]\" 형식으로 입력해주세요.\nex) \"/search 보라매 주말 [추가검색어]\"'
        elif command == '/yeyak':
            if facility_name is not None and weektime is not None and weektime in ['평일', '주말']:
                # Send first message
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

                # Final message
                title, body = f'예약 완료됐습니다!', '(예약정보)'
        elif command == '/disconnect':
            self._delete_session()
            title = f'Bye, {self.username}'

        return title, body

    def _execute_yeyak(self, command: str, **kwargs):
        """
        Facility Reservation.
        Target Facility -> song-pa, jamsil, boramae
        Reserve Time -> Saturday 7th and 8th quarter / Sunday 3rd, 4th and 5th quarter (12th, 13th, 14th)

        Take action and Return response_title, response_body for telegram chat.
        If there is nothing to respond to, it can return a Tuple object filled with None.
        """
        title, body = None, None

        if command != '/yeyak':  # Only work with '/yeyak' command
            return title, body

        # Send init message
        self.set_response(resp_title=f'예약 가능한 시설을 검색합니다. (최대 100회 탐색)')
        self.send_response()

        # Open domain site in browser
        yeyak_handler = YeyakHandler()
        if 'test' in kwargs and kwargs['test']:
            yeyak_handler.test = kwargs['test']
        yeyak_handler.open()

        # Search and Reserve valid facility
        target, quarter = ('송파구여성', '잠실유수지', '보라매'), (7, 8, 12, 13, 14)  # TODO: Make these to CONFIG variables
        for result in yeyak_handler.yeyak(target, quarter, self.username):  # Use generator
            if result and isinstance(result, int):
                self.set_response(resp_title=f'{result}회 검색중...')
                self.send_response()
            elif result and isinstance(result, Tuple) and len(result) == 2:  # title, body
                title, body = result

        # Close and Quit browser
        yeyak_handler.quit()

        # Final message
        return title, body

    def action_by_step(self) -> Union[Dict, List]:
        """Take action and Return send_result."""
        if self.bot_status == 2:  # Status of bot_command
            command, *args = self.text.split(' ')
            if command == '/start':
                title = f'하이, {self.username}👋. 예약 봇을 시작합니다.'
                body = '예약하려면 "/yeyak" 을, 테스트하려면 "/testyeyak" 을 입력하세요.'
            elif command == '/yeyak':  # Reserve at once
                title, body = self._execute_yeyak(command)
            elif command == '/testyeyak':  # Check possibility
                title, body = self._execute_yeyak(command='/yeyak', test=True)
            elif command == '/disconnect':
                title, body = f'Bye, {self.username}', None
            else:  # Legacy condition
                title, body = self._make_contents(command, *args)
            self.set_response(resp_title=title, resp_body=body)

        send_result = self.send_response()
        return {'ok': send_result}
