from parsing_helper.web_elements import ExtendedWebElement, ExtendedWebElementCollection
from selenium.webdriver import Remote

from .wildberries_base_page import WildberriesPage


# page_url = https://www.wildberries.ru/security/login
class LogInPage(WildberriesPage):
    path = "security/login"

    def __init__(self, parser, authorization_driver: Remote = None) -> None:
        super().__init__(parser)
        self.authorization_driver = authorization_driver

        self.geo_link = ExtendedWebElement(self, '//span[contains(@class, "geocity-link")]')
        self.main_banner_container = ExtendedWebElement(
            self,
            '//div[contains(@class, "swiper-container j-main-banners")]'
        )
        self.phone_number_input = ExtendedWebElement(self, '//input[@class = "input-item"]')
        self.get_code_button = ExtendedWebElement(self, '//button[@id = "requestCode"]')
        # noinspection SpellCheckingInspection
        self.code_inputs = ExtendedWebElementCollection(self, '//input[@class = "input-item j-b-charinput"]')
