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

    @deprecated
    def _execute_onestep(self, command: str, **kwargs):
        import time
        import functools

        from selenium.webdriver import Chrome, ChromeOptions
        from selenium.webdriver.support.ui import Select

        CHROME_DRIVER_PATH = CONFIG['VAL']['selenium']['path.chromedriver']
        AUTH_CONF = CONFIG['AUTH']['reservation']
        CHROME_YEYAK_CONF = CONFIG['VAL']['seoul.yeyak']['chrome']

        title, body = None, None

        if command != '/yeyak':  # Only work with '/yeyak' command
            return title, body

        # Send init message
        self.set_response(resp_title=f'예약 가능한 시설을 검색합니다. (최대 100회 탐색)')
        self.send_response()

        # Go to yeyak
        test = False
        if 'test' in kwargs and kwargs['test']:
            test = kwargs['test']
        options = ChromeOptions()
        options.add_argument('window-size=1600,1024')
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')
        driver = Chrome(executable_path=CHROME_DRIVER_PATH, options=options)

        # Open domain site in browser
        default_url = CHROME_YEYAK_CONF['url']
        driver.get(default_url if default_url else 'https://yeyak.seoul.go.kr')

        # Search and Reserve valid facility
        target, quarter = ('송파구여성', '잠실유수지', '보라매'), (7, 8, 12, 13, 14)  # TODO: Make these to CONFIG variables
        target_weekend = ('주말', '토, ', ', 일')
        quarter_start_times = tuple([q*2+4 for q in quarter])  # Translate to time quarter

        # Set to version of Korean
        driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.lang_tit']).click()
        driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.lang_kor']).click()
        time.sleep(2)

        # Login action
        driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.btn_login']).click()
        input_userid = driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.input_userid'])
        input_userid.send_keys(AUTH_CONF['seoul.yeyak.id'])
        input_password = driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.input_password'])
        input_password.send_keys(AUTH_CONF['seoul.yeyak.password'])
        driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.btn_login_submit']).click()

        # Search by target
        soccer_code, cnt = 'T105', 0
        while cnt < 100:
            # Select facility type to soccer
            time.sleep(1)
            select_facility_type = driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.select_facility_type'])
            Select(select_facility_type).select_by_value(soccer_code)
            time.sleep(2)

            # Search option by target
            select_elem = driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.select_facilities'])
            facilities = select_elem.find_elements_by_tag_name('option')
            options = [
                (option.get_property('value'), option.text)
                for option in facilities
                # Whether the facility-name(option.text) contains target keywords and target weekend keywords
                if functools.reduce(
                    lambda x, y: x or y,
                    [keyword in option.text for keyword in target]
                ) and functools.reduce(
                    lambda x, y: x or y,
                    [weekend_keyword in option.text for weekend_keyword in target_weekend])
            ]
            if options:
                LOGGER.info(f'[YEYAK] searched! > {options}')
                # Check and Registration!!
                result = self._register_facility(driver, options, select_elem, quarter_start_times, self.username, test)
                if result[0] is not None and result[1] is not None:  # if contents existing
                    if result and isinstance(result, Tuple) and len(result) == 2:  # title, body
                        title, body = result
                    LOGGER.info(f'[YEYAK] Done.')
                    LOGGER.info(f'[YEYAK] TITLE: {result[0]}')
                    LOGGER.info(f'[YEYAK] BODY: {result[1]}')
                    break

            # Yield every 10 count
            if cnt % 10 == 9:
                cnt += 1
                self.set_response(resp_title=f'{cnt}회 검색중...')
                self.send_response()
                continue

            # Reload page
            LOGGER.info(f'[YEYAK][{cnt + 1}] no result. refresh page')
            time.sleep(1)
            driver.get(default_url if default_url else 'https://yeyak.seoul.go.kr')  # Open home site
            cnt += 1

        # Logout action
        driver.find_element_by_xpath(CHROME_YEYAK_CONF['xpath.btn_logout']).click()

        # Close and Quit browser
        driver.quit()

        # Final message
        return title, body

    def _register_facility(self, driver, options, select_elem, quarter_start_times, username, test):
        import time
        import pytz

        from datetime import datetime, timedelta
        from selenium.webdriver.support.ui import Select

        # Check daily quarter(time area) matched by each option
        for option in options:
            # Select option and Go to reservation page (예약하기(1))
            option_value, facility_name = option
            Select(select_elem).select_by_value(option_value)
            driver.find_element_by_xpath(
                '/html/body/div/div[3]/div[1]/div[1]/div/div/div[2]/div[1]/button').click()

            # Clear all popup
            for popup in driver.find_elements_by_class_name('pop_x'):
                LOGGER.info(f'[YEYAK] Click existing popup')
                try:
                    popup.click()
                except Exception:
                    LOGGER.error(f'[YEYAK] An error occurred clicking popup button')

            # Go to detailed reservation page (예약하기(2))
            driver.find_element_by_xpath(
                '/html/body/div/div[3]/div[2]/div/form[2]/div[1]/div[2]/div/div/a[1]').click()

            # Select specific schedule matched (daily -> timely)
            for daily_elem in driver.find_elements_by_class_name('tbl_cal .able'):
                daily_elem_tag_a = daily_elem.find_element_by_tag_name('a')

                # TODO: Move to datetimelib.py
                KST_TZ = pytz.timezone('Asia/Seoul')
                curr_datetime_kst = datetime.utcnow().replace(tzinfo=pytz.timezone('UTC')).astimezone(tz=KST_TZ)
                selected_date_kst = KST_TZ.localize(  # Get selected date as KST
                    datetime.strptime(daily_elem_tag_a.get_attribute('data-ymd'), '%Y%m%d'))

                selected_weekday = selected_date_kst.weekday()
                # Check weekends except today
                if curr_datetime_kst.date() != selected_date_kst.date() and selected_weekday >= 5:
                    daily_elem_tag_a.click()
                    for timely_elem in driver.find_elements_by_class_name('tab-all'):
                        timely_elem_tag_a = timely_elem.find_element_by_tag_name('a')
                        start_hour = int(timely_elem_tag_a.get_attribute('data-start-hm').split(':')[0])
                        if selected_weekday == 6:  # Adjust start_hour for sunday
                            start_hour += 18

                        # Check for quarter time matched
                        if start_hour in quarter_start_times:
                            timely_elem_tag_a.click()

                            # Additioanl info
                            group_name = 'FC Tesla'
                            register_email_id = 'yyy123789'
                            register_email_domain = 'naver.com'
                            register_date = (selected_date_kst + timedelta(
                                hours=start_hour - 18 if selected_weekday == 6 else start_hour
                            )).strftime('%Y-%m-%d %H:%M:%S')

                            LOGGER.info(f'[YEYAK] START-HOUR-MATCHED: '
                                        f'{register_date} -> ({selected_weekday}){start_hour}')

                            driver.find_element_by_class_name('user_plus').click()  # 이용인원
                            for e in driver.find_elements_by_class_name('book_tit2 label'):  # 신청자 정보와 동일, 전체동의
                                try:
                                    e.click()
                                except Exception:
                                    LOGGER.error(f'[YEYAK] An error occurred clicking label for, '
                                                 f'"chk_info", "chk_agree_all"')
                            try:
                                driver.find_element_by_xpath(
                                    '/html/body/div/div[3]/div[2]/div/div[1]/form/div[3]'
                                    '/div[2]/div[5]/table/tbody/tr[1]/td/span[2]/label'
                                ).click()  # Select radio label for '단체'
                            except Exception:
                                LOGGER.exception(f'There is no radio element for "단체"')
                            driver.find_element_by_id('grp_nm').send_keys(group_name)  # 단체명
                            driver.find_element_by_id('form_email1').send_keys(register_email_id)  # 이메일
                            driver.find_element_by_id('form_email2').send_keys(register_email_domain)

                            # Yeyak for matched target if not in test mode!!
                            if not test:
                                driver.find_element_by_xpath(
                                    '/html/body/div/div[3]/div[2]/div/div[1]/form/div[3]/div[3]/div/div[3]/button'
                                ).click()
                                driver.switch_to.alert.accept()  # Pass existing alert

                            time.sleep(3)

                            # Return reservation message
                            return f'{"[TEST] " if test else ""}예약 완료!', \
                                   f'- 시설명: {facility_name}\n' \
                                   f'- 일시: {register_date}\n' \
                                   f'- 예약자명: {username}\n' \
                                   f'- 예약 이메일: {register_email_id}@{register_email_domain}'
        return None, None

    def action_by_step(self) -> Union[Dict, List]:
        """Take action and Return send_result."""
        if self.bot_status == 2:  # Status of bot_command
            command, *args = self.text.split(' ')
            if command == '/start':
                title = f'하이, {self.username}👋. 예약 봇을 시작합니다.'
                body = '예약하려면 "/yeyak" 을, 테스트하려면 "/testyeyak" 을 입력하세요.'
            elif command == '/yeyak':  # Reserve at once
                # title, body = self._execute_onestep(command)
                title, body = self._execute_yeyak(command)
            elif command == '/testyeyak':  # Check possibility
                # title, body = self._execute_onestep(command='/yeyak', test=True)
                title, body = self._execute_yeyak(command='/yeyak', test=True)
            elif command == '/disconnect':
                title, body = f'Bye, {self.username}', None
            else:  # Legacy condition
                title, body = self._make_contents(command, *args)
            self.set_response(resp_title=title, resp_body=body)

        send_result = self.send_response()
        return {'ok': send_result}
