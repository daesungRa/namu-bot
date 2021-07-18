"""
Namu's custom selenium library classes.
MAINTAINER: Ra Daesung (daesungra@gmail.com)
"""

import logging
from typing import Optional, Type

from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver import Chrome, ChromeOptions
from selenium.common.exceptions import WebDriverException

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

        driver.implicitly_wait(5)
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


class ChromeDriverHandler(SeleniumHandler):
    def __init__(self, url: str = None):
        """Set and Handling Chrome webdriver."""
        try:
            options = ChromeOptions()
            options.add_argument('window-size=1920,1080')
            driver = Chrome(executable_path=CHROME_DRIVER_PATH, options=options)
        except WebDriverException:
            raise WebDriverPathError(path=CHROME_DRIVER_PATH)

        super().__init__(driver=driver, driver_not_found_error=ChromeDriverNotFoundError, url=url)
