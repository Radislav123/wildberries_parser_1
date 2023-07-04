from typing import TYPE_CHECKING

from parsing_helper.pages import BasePage
from selenium.webdriver import Chrome


if TYPE_CHECKING:
    from core.parser import ParserCore


# page_url = https://www.wildberries.ru/
class WildberriesPage(BasePage):
    scheme = "https"
    domain = "www.wildberries.ru"
    path = ""

    # todo: перевести страницы из web_helper на использование parser
    def __init__(self, parser: "ParserCore"):
        # todo: use parsing_helper.base_page.BasePage.parser
        self.parser = parser
        # todo: use parsing_helper.base_page.BasePage.settings
        self.settings = self.parser.settings
        # todo: use parsing_helper.base_page.BasePage.logger
        self.logger = self.parser.logger
        super().__init__(self.parser.driver)

    def transfer_cookies(self, donor_driver: Chrome):
        self.open()
        for cookie in donor_driver.get_cookies():
            self.driver.add_cookie(cookie)
        self.open()
