import logging
import functools
import pytz
from datetime import datetime, timedelta, time
from typing import Tuple, Optional

from selenium.webdriver.common.keys import Keys

from apps.flasklib import deprecated
from apps.seleniumlib import ChromeDriverHandler

from config import CONFIG


LOGGER = logging.getLogger(__name__)
AUTH_CONF = CONFIG['AUTH']['reservation']
CHROME_YEYAK_CONF = CONFIG['VAL']['seoul.yeyak']['chrome']
FIREFOX_YEYAK_CONF = CONFIG['VAL']['seoul.yeyak']['firefox']


class YeyakHandler(ChromeDriverHandler):
    def __init__(self):
        super().__init__(url=CHROME_YEYAK_CONF['url'])

    def login(self, userid: str = None, password: str = None):
        # Go to login page
        elem = self.search_by_xpath(CHROME_YEYAK_CONF['xpath.btn_login'])
        self.click_elem(elem=self.search_by_xpath(CHROME_YEYAK_CONF['xpath.btn_login']))

        # Insert id, pwd
        input_userid = self.search_by_xpath(CHROME_YEYAK_CONF['xpath.input_userid'])
        self.send_keys_to_elem(
            elem=input_userid,
            key=userid if userid else AUTH_CONF['seoul.yeyak.id']
        )
        input_password = self.search_by_xpath(CHROME_YEYAK_CONF['xpath.input_password'])
        self.send_keys_to_elem(
            elem=input_password,
            key=password if password else AUTH_CONF['seoul.yeyak.password']
        )

        # Click submit button
        self.click_elem(self.search_by_xpath(CHROME_YEYAK_CONF['xpath.btn_login_submit']))

    def logout(self):
        # Click logout button
        self.click_elem(self.search_by_xpath(CHROME_YEYAK_CONF['xpath.btn_logout']))

    @deprecated
    def search_facility(self, facility_name: str, weektime: str, additional_word: str = None):
        LOGGER.info(f'[SEARCH] Start searching with {facility_name}, {weektime}...')

        options, cnt = [], 0
        soccer_code = 'T107'
        # Repeat until 100 count
        while cnt < 100:
            # Select facility type to soccer
            self.action_select(self.search_by_xpath(CHROME_YEYAK_CONF['xpath.select_facility_type']), soccer_code)
            self.sleep(2)

            # Search option by inserted param
            select_elem = self.search_by_xpath(CHROME_YEYAK_CONF['xpath.select_facilities'])
            options = [
                (option.get_property('value'), option.text)
                for option in select_elem.find_elements_by_tag_name('option')
                if facility_name in option.text and weektime in option.text
            ]

            # Match additional word
            if additional_word:
                options = [o for o in options if additional_word in o[1]]

            # Return and Break if options is not empty
            if options:
                LOGGER.info(f'[SEARCH] searched! > {options}')
                yield options
                break

            # Yield every 10 count
            if cnt % 10 == 9:
                yield cnt + 1

            # Reload page
            LOGGER.info(f'[SEARCH][{cnt + 1}] no result. refresh page')
            self.sleep(1)
            self.refresh()
            cnt += 1

        LOGGER.info(f'[SEARCH] Done. search count of {len(options)}')

    @deprecated
    def yeyak_facility(self, facility_name: str, weektime: str, additional_word: str = None):
        word = f', {additional_word}'
        LOGGER.info(
            f'[YEYAK] Start reservation with '
            f'{facility_name}, {weektime}{additional_word and word or ""}...'
        )

        # Select facility type to soccer
        soccer_code = 'T107'
        self.action_select(self.search_by_xpath(CHROME_YEYAK_CONF['xpath.select_facility_type']), soccer_code)
        self.sleep(2)

        # Select option by inserted param
        select_elem = self.search_by_xpath(CHROME_YEYAK_CONF['xpath.select_facilities'])
        options = [
            (option.get_property('value'), option.text)
            for option in select_elem.find_elements_by_tag_name('option')
            if facility_name in option.text and weektime in option.text
        ]
        if options:
            # Select correct option with param
            option_selected = options[0]
            if len(options) > 1 and additional_word:
                for o in options:
                    if additional_word in o[1]:  # Compare with option text
                        option_selected = o
            LOGGER.info(f'[YEYAK] Select info > {option_selected}')
            self.action_select(select_elem, option_selected[0])  # Select by option value

            # Click 에약하기 main
            self.click_elem(self.search_by_xpath('/html/body/div/div[3]/div[1]/div[1]/div/div/div[2]/div[1]/button'))

            # Clear all popup
            for popup in self.search_many_by_class_name('pop_x'):
                LOGGER.info(f'[YEYAK] Click existing popup')
                try:
                    self.click_elem(popup)
                except Exception:
                    LOGGER.error(f'[YEYAK] An error occurred clicking popup button')

            # Click 예약하기 second
            self.click_elem(self.search_by_xpath('/html/body/div/div[3]/div[2]/div/form[2]/div[1]/div[2]/div/div/a[1]'))

            # Select specific schedule
            self.click_elem(self.search_many_by_class_name('able')[1].find_element_by_tag_name('a'))
            self.click_elem(self.search_many_by_class_name('tab-all')[0].find_element_by_tag_name('a'))

            # Additioanl info
            self.click_elem(self.search_by_class_name('user_plus'))  # 이용인원
            for e in self.search_many_by_class_name('book_tit2 label'):  # 신청자 정보와 동일, 전체동의
                try:
                    self.click_elem(e)
                except Exception:
                    LOGGER.error(f'[YEYAK] An error occurred clicking label for, "chk_info", "chk_agree_all"')
            self.send_keys_to_elem(self.search_by_id('grp_nm'), 'hahaha')  # 단체명
            self.send_keys_to_elem(self.search_by_id('form_email1'), 'hahahaha')  # 이메일1
            self.send_keys_to_elem(self.search_by_id('form_email2'), 'gmail.com')  # 이메일2

            self.sleep(3)

    def yeyak(self, target: Optional[Tuple], quarter: Optional[Tuple], username: str) -> Optional[Tuple]:
        title, body = '검색 결과가 없습니다. 다시 시도해 주세요.', None

        # Set to version of Korean
        self.click_elem(self.search_by_xpath(CHROME_YEYAK_CONF['xpath.lang_tit']))
        self.click_elem(self.search_by_xpath(CHROME_YEYAK_CONF['xpath.lang_kor']))
        self.sleep(2)

        if not target:
            target = ('송파구여성', '잠실유수지', '보라매')
        target_weekend = ('주말', '토, ', ', 일')

        if not quarter:
            quarter = (7, 8, 12, 13, 14)
        quarter_start_times = tuple([q*2+4 for q in quarter])  # Translate to time quarter

        # Login action
        self.login()

        # Search by target
        soccer_code, cnt = 'T107', 0
        while cnt < 100:
            # Select facility type to soccer
            self.action_select(self.search_by_xpath(CHROME_YEYAK_CONF['xpath.select_facility_type']), soccer_code)
            self.sleep(2)

            # Search option by target
            select_elem = self.search_by_xpath(CHROME_YEYAK_CONF['xpath.select_facilities'])
            options = [
                (option.get_property('value'), option.text)
                for option in self.search_many_by_tag_name('option', select_elem)
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
                result = self._register_facility(options, select_elem, quarter_start_times, username)
                if result[0] is not None and result[1] is not None:  # if contents existing
                    yield result
                    LOGGER.info(f'[YEYAK] Done.')
                    LOGGER.info(f'[YEYAK] TITLE: {result[0]}')
                    LOGGER.info(f'[YEYAK] BODY: {result[1]}')
                    break

            # Yield every 10 count
            if cnt % 10 == 9:
                yield cnt + 1

            # Reload page
            LOGGER.info(f'[YEYAK][{cnt + 1}] no result. refresh page')
            self.sleep(1)
            self.open()  # Open home site
            cnt += 1

        # Logout action
        self.logout()

    def _register_facility(self, options, select_elem, quarter_start_times, username):
        # Check daily quarter(time area) matched by each option
        for option in options:
            # Select option and Go to reservation page (예약하기(1))
            option_value, facility_name = option
            self.action_select(select_elem, option_value)
            self.click_elem(
                self.search_by_xpath('/html/body/div/div[3]/div[1]/div[1]/div/div/div[2]/div[1]/button'))

            # Clear all popup
            for popup in self.search_many_by_class_name('pop_x'):
                LOGGER.info(f'[YEYAK] Click existing popup')
                try:
                    self.click_elem(popup)
                except Exception:
                    LOGGER.error(f'[YEYAK] An error occurred clicking popup button')

            # Go to detailed reservation page (예약하기(2))
            self.click_elem(self.search_by_xpath(
                '/html/body/div/div[3]/div[2]/div/form[2]/div[1]/div[2]/div/div/a[1]'))

            # Select specific schedule matched (daily -> timely)
            for daily_elem in self.search_many_by_class_name('tbl_cal .able'):
                daily_elem_tag_a = self.search_by_tag_name('a', daily_elem)

                # TODO: Move to datetimelib.py
                KST_TZ = pytz.timezone('Asia/Seoul')
                curr_datetime_kst = datetime.utcnow().replace(tzinfo=pytz.timezone('UTC')).astimezone(tz=KST_TZ)
                selected_date_kst = KST_TZ.localize(  # Get selected date as KST
                    datetime.strptime(daily_elem_tag_a.get_attribute('data-ymd'), '%Y%m%d'))

                selected_weekday = selected_date_kst.weekday()
                # Check weekends except today
                if curr_datetime_kst.date() != selected_date_kst.date() and selected_weekday >= 5:
                    self.click_elem(daily_elem_tag_a)
                    for timely_elem in self.search_many_by_class_name('tab-all'):
                        timely_elem_tag_a = self.search_by_tag_name('a', timely_elem)
                        start_hour = int(timely_elem_tag_a.get_attribute('data-start-hm').split(':')[0])
                        if selected_weekday == 6:  # Adjust start_hour for sunday
                            start_hour += 18

                        # Check for quarter time matched
                        if start_hour in quarter_start_times:
                            self.click_elem(timely_elem_tag_a)

                            # Additioanl info
                            group_name = 'FC Tesla'
                            register_email_id = 'yyy123789'
                            register_email_domain = 'naver.com'
                            register_date = (selected_date_kst + timedelta(
                                hours=start_hour - 18 if selected_weekday == 6 else start_hour
                            )).strftime('%Y-%m-%d %H:%M:%S')

                            LOGGER.info(f'[YEYAK] START-HOUR-MATCHED: '
                                        f'{register_date} -> ({selected_weekday}){start_hour}')

                            self.click_elem(self.search_by_class_name('user_plus'))  # 이용인원
                            for e in self.search_many_by_class_name('book_tit2 label'):  # 신청자 정보와 동일, 전체동의
                                try:
                                    self.click_elem(e)
                                except Exception:
                                    LOGGER.error(f'[YEYAK] An error occurred clicking label for, '
                                                 f'"chk_info", "chk_agree_all"')
                            try:
                                self.click_elem(
                                    self.search_by_xpath('/html/body/div/div[3]/div[2]/div/div[1]/form/div[3]'
                                                         '/div[2]/div[5]/table/tbody/tr[1]/td/span[2]/label')
                                )  # Select radio label for '단체'
                            except Exception:
                                LOGGER.exception(f'There is no radio element for "단체"')
                            self.send_keys_to_elem(self.search_by_id('grp_nm'), group_name)  # 단체명
                            self.send_keys_to_elem(self.search_by_id('form_email1'), register_email_id)  # 이메일
                            self.send_keys_to_elem(self.search_by_id('form_email2'), register_email_domain)

                            # Yeyak for matched target if not in test mode!!
                            if not self.test:
                                self.click_elem(self.search_by_xpath(  # Click final yeyak button
                                    '/html/body/div/div[3]/div[2]/div/div[1]/form/div[3]/div[3]/div/div[3]/button'))
                                self.driver.switch_to.alert.accept()  # Pass existing alert

                            self.sleep(3)

                            # Return reservation message
                            return f'{"[TEST] " if self.test else ""}예약 완료!', \
                                   f'- 시설명: {facility_name}\n' \
                                   f'- 일시: {register_date}\n' \
                                   f'- 예약자명: {username}\n' \
                                   f'- 예약 이메일: {register_email_id}@{register_email_domain}'
        return None, None
