from typing import TYPE_CHECKING

from selenium.webdriver import Chrome

from ..base_page import BasePage


if TYPE_CHECKING:
    from parser.wildberries_parser import SecretKeeper


# page_url = https://www.wildberries.ru/
class WildberriesPage(BasePage):
    scheme = "https"
    domain = "www.wildberries.ru"
    path = ""

    def __init__(self, driver: Chrome):
        super().__init__(driver)

    def authorize_and_open(self, cookie: "SecretKeeper.Cookie"):
        self.open()
        self.driver.add_cookie(cookie.to_dict())
        self.open()
