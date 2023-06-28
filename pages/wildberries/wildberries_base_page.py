from parsing_helper.pages import BasePage
from selenium.webdriver import Chrome

from parser.settings import Settings


# page_url = https://www.wildberries.ru/
class WildberriesPage(BasePage):
    scheme = "https"
    domain = "www.wildberries.ru"
    path = ""

    def __init__(self, driver: Chrome, settings: Settings):
        super().__init__(driver)
        # todo: use parsing_helper.base_page.BasePage.settings
        self.settings = settings

    def transfer_cookies(self, donor_driver: Chrome):
        self.open()
        for cookie in donor_driver.get_cookies():
            self.driver.add_cookie(cookie)
        self.open()
