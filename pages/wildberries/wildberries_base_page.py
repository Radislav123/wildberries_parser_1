from typing import Self, TYPE_CHECKING

from parsing_helper.pages import BasePage
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import BaseWebDriver


if TYPE_CHECKING:
    from core.parser import ParserCore


# page_url = https://www.wildberries.ru/
class WildberriesPage(BasePage):
    scheme = "https"
    domain = "www.wildberries.ru"
    path = ""

    # todo: перевести страницы из web_helper на использование parser и BaseWebDriver
    def __init__(self, parser: "ParserCore"):
        if not isinstance(parser, BaseWebDriver):
            # todo: use parsing_helper.base_page.BasePage.parser
            self.parser = parser
            # todo: use parsing_helper.base_page.BasePage.settings
            self.settings = self.parser.settings
            # todo: use parsing_helper.base_page.BasePage.logger
            self.logger = self.parser.logger
            super().__init__(self.parser.driver)
        else:
            # todo: use parsing_helper.base_page.BasePage.parser
            self.parser = None
            # todo: use parsing_helper.base_page.BasePage.settings
            self.settings = None
            # todo: use parsing_helper.base_page.BasePage.logger
            self.logger = None
            # parser == driver
            super().__init__(parser)

    @classmethod
    def create_without_parser(cls, driver: Chrome) -> Self:
        # noinspection PyTypeChecker
        return cls(driver)

    def transfer_cookies(self, donor_driver: Chrome):
        self.open()
        for cookie in donor_driver.get_cookies():
            self.driver.add_cookie(cookie)
        self.open()
