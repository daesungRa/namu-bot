"""
Namu's custom selenium library classes.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
import functools
from typing import Union, Optional, Type
from time import sleep

from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import Chrome, ChromeOptions
from selenium.common.exceptions import WebDriverException, UnexpectedAlertPresentException

from selenium.webdriver.support.ui import Select

from config import CONFIG


LOGGER = logging.getLogger(__name__)
CHROME_DRIVER_PATH = CONFIG['VAL']['selenium']['path.chromedriver']


class WebDriverPathError(WebDriverException):
    def __init__(self, path: str):
        super().__init__(msg=f"Wrong web driver path. path is '{path}'")


class WebDriverNotFoundError(WebDriverException):
    driver_type: Optional[str] = None

    def __init__(self):
        super().__init__(msg=f'{self.driver_type} driver not set.')


class UrlNotFoundError(WebDriverException):
    def __init__(self):
        super().__init__(msg=f'No url for open.')


class ChromeDriverNotFoundError(WebDriverNotFoundError):
    driver_type = 'Chrome'


class SeleniumHandler:
    driver: Optional[RemoteWebDriver] = None
    driver_not_found_error: Type[WebDriverNotFoundError] = WebDriverNotFoundError
    url: Optional[str] = None

    def __init__(self,
                 driver: RemoteWebDriver,
                 driver_not_found_error: Type[WebDriverNotFoundError] = WebDriverNotFoundError,
                 url: str = None):
        """
        This is default handler for selenium webdriver.
        This can be inherited according to the browser type.

        :param driver:
            RemoteWebDriver type object for the specific browser specified in subclass.

        TODO: self.url must be set as the default web domain in the subclass or instance.
        """
        assert driver is not None

        driver.implicitly_wait(time_to_wait=5)
        self.driver = driver

        if driver_not_found_error:
            self.driver_not_found_error = driver_not_found_error
        if url:
            self.url = url

        LOGGER.info(f'Chrome webdriver handler is set.')

    def open(self, url: str = None):
        """Open web browser using self.driver and open_url."""
        if self.driver is None or not isinstance(self.driver, RemoteWebDriver):
            raise self.driver_not_found_error

        open_url = url if url else self.url
        if open_url is None:
            raise UrlNotFoundError

        self.driver.get(open_url)
        LOGGER.info(f'URL opened by webdriver.')

    def quit(self):
        """Close opened web browser."""
        if self.driver is not None and isinstance(self.driver, RemoteWebDriver) and self.driver.current_url:
            curr_url = self.driver.current_url
            self.driver.quit()
            LOGGER.info(f"Webdriver is closed. current_url is '{curr_url}'")

    def sleep(self, sec: Union[int, float] = 1):
        """
        Interval sleep by sec

        :param sec: it can be of type int or float. default is 1.
        """
        sleep(sec)

    def refresh(self):
        self.driver.refresh()

    def search_by_class_name(self, class_name: str): pass

    def search_many_by_class_name(self, class_name: str): pass

    def search_by_id(self, id_val: str): pass

    def search_by_xpath(self, xpath: str): pass

    def send_keys_to_elem(self, elem: WebElement, key: str): pass

    def click_elem(self, elem: WebElement): pass

    def action_select(self, elem: WebElement, code: str): pass


def deco_search_action(func):
    """Decorate selenium action"""
    @functools.wraps(func)
    def _wrapper(self: SeleniumHandler, search_key: str, elem: WebElement = None, *args, **kwargs):
        # TODO: Add more necessary pre_process
        assert search_key is not None and isinstance(search_key, str)
        return func(self, search_key, elem, *args, **kwargs)
    return _wrapper


def deco_elem_action(func):
    """Decorate selenium action"""
    @functools.wraps(func)
    def _wrapper(self: SeleniumHandler, elem: WebElement, *args, **kwargs):
        # TODO: Add more necessary pre_process
        assert elem is not None and isinstance(elem, WebElement)
        try:
            return func(self, elem, *args, **kwargs)
        except UnexpectedAlertPresentException as uae:
            LOGGER.exception(f'Unexpected Alert Error occurred: {uae}')
            self.driver.switch_to.alert.accept()
            # Try again after alert clear
            return func(self, elem, *args, **kwargs)
    return _wrapper


class ChromeDriverHandler(SeleniumHandler):
    def __init__(self, url: str = None):
        """Set and Handling Chrome webdriver."""
        try:
            options = ChromeOptions()
            options.add_argument('window-size=1600,1024')
            # options.add_argument('window-size=1920,1080')
            # options.add_argument('--headless')
            # options.add_argument('--no-sandbox')
            # options.add_argument('--disable-gpu')
            # options.add_argument('--disable-dev-shm-usage')
            # options.add_argument('--disable-extensions')
            # options.add_argument("--ignore-certificate-errors")
            # options.add_argument("--disable-popup-blocking")
            driver = Chrome(executable_path=CHROME_DRIVER_PATH, options=options)
        except WebDriverException:
            raise WebDriverPathError(path=CHROME_DRIVER_PATH)

        super().__init__(driver=driver, driver_not_found_error=ChromeDriverNotFoundError, url=url)

    @deco_search_action
    def search_by_class_name(self, class_name: str, elem: WebElement = None):
        if elem is not None:
            return elem.find_element_by_class_name(class_name)
        return self.driver.find_element_by_class_name(class_name)

    @deco_search_action
    def search_many_by_class_name(self, class_name: str, elem: WebElement = None):
        if elem is not None:
            return elem.find_elements_by_class_name(class_name)
        return self.driver.find_elements_by_class_name(class_name)

    @deco_search_action
    def search_by_id(self, id_val: str, elem: WebElement = None):
        if elem is not None:
            return elem.find_element_by_id(id_val)
        return self.driver.find_element_by_id(id_val)

    @deco_search_action
    def search_by_xpath(self, xpath: str, elem: WebElement = None):
        if elem is not None:
            return elem.find_element_by_xpath(xpath)
        return self.driver.find_element_by_xpath(xpath)

    @deco_elem_action
    def send_keys_to_elem(self, elem: WebElement, key: str):
        elem.send_keys(key)

    @deco_elem_action
    def click_elem(self, elem: WebElement):
        elem.click()

    @deco_elem_action
    def action_select(self, elem: WebElement, code: str):
        Select(elem).select_by_value(code)
