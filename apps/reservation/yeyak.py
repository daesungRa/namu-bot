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

        # Select facility type to soccer
        options, cnt = [], 0
        soccer_code = 'T107'
        while cnt < 100:
            # Repeat until 100 count
            self.action_select(self.search_by_xpath(YEYAK_CONF['xpath.select_facility_type']), soccer_code)
            self.sleep(2)

            # Search option by facility name
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
