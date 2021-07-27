import logging

from selenium.webdriver.common.keys import Keys

from apps.seleniumlib import ChromeDriverHandler

from config import CONFIG


LOGGER = logging.getLogger(__name__)
AUTH_CONF = CONFIG['AUTH']['reservation']
YEYAK_CONF = CONFIG['VAL']['seoul.yeyak']


class YeyakHandler(ChromeDriverHandler):
    def __init__(self):
        super().__init__(url=YEYAK_CONF['url'])

    def login(self, userid: str = None, password: str = None):
        # Go to login page
        elem = self.search_by_xpath(YEYAK_CONF['xpath.btn_login'])
        self.click_elem(elem=self.search_by_xpath(YEYAK_CONF['xpath.btn_login']))

        # Insert id, pwd
        input_userid = self.search_by_xpath(YEYAK_CONF['xpath.input_userid'])
        self.send_keys_to_elem(
            elem=input_userid,
            key=userid if userid else AUTH_CONF['seoul.yeyak.id']
        )
        input_password = self.search_by_xpath(YEYAK_CONF['xpath.input_password'])
        self.send_keys_to_elem(
            elem=input_password,
            key=password if password else AUTH_CONF['seoul.yeyak.password']
        )

        # Click submit button
        self.click_elem(self.search_by_xpath(YEYAK_CONF['xpath.btn_login_submit']))

    def logout(self):
        # Click logout button
        self.click_elem(self.search_by_xpath(YEYAK_CONF['xpath.btn_logout']))

    def search_facility(self, facility_name: str, weektime: str):
        LOGGER.info(f'[SEARCH] Start searching with {facility_name}, {weektime}...')

        options, cnt = [], 0
        soccer_code = 'T107'
        # Repeat until 100 count
        while cnt < 100:
            # Select facility type to soccer
            self.action_select(self.search_by_xpath(YEYAK_CONF['xpath.select_facility_type']), soccer_code)
            self.sleep(2)

            # Search option by inserted param
            select_elem = self.search_by_xpath(YEYAK_CONF['xpath.select_facilities'])
            options = [
                option.text
                for option in select_elem.find_elements_by_tag_name('option')
                if facility_name in option.text and weektime in option.text
            ]
            if options:
                LOGGER.info(f'[SEARCH] searched! > {options}')
                break

            # Reload page
            LOGGER.info(f'[SEARCH][{cnt + 1}] no result. refresh page')
            self.sleep(1)
            self.refresh()
            cnt += 1

        LOGGER.info(f'[SEARCH] Done. search count of {len(options)}')
        return options

    def yeyak_facility(self, facility_name: str, weektime: str, additional_word: str = None):
        word = f', {additional_word}'
        LOGGER.info(
            f'[YEYAK] Start reservation with '
            f'{facility_name}, {weektime}{additional_word and word or ""}...'
        )

        # Select facility type to soccer
        soccer_code = 'T107'
        self.action_select(self.search_by_xpath(YEYAK_CONF['xpath.select_facility_type']), soccer_code)
        self.sleep(2)

        # Select option by inserted param
        select_elem = self.search_by_xpath(YEYAK_CONF['xpath.select_facilities'])
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
