from parsing_helper.web_elements import ExtendedWebElement
from selenium.webdriver import Chrome

from parser.settings import Settings
from .wildberries_base_page import WildberriesPage


# page_url = https://www.wildberries.ru/lk/details
class LKDetailsPage(WildberriesPage):
    path = "lk/details"

    def __init__(self, driver: Chrome, settings: Settings) -> None:
        super().__init__(driver, settings)
        self.personal_sale = ExtendedWebElement(self, '//b[@class = "discount__numb discount__numb--color"]')
