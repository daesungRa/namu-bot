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
