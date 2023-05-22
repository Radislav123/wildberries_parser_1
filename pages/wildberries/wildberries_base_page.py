from selenium.webdriver import Chrome

from ..base_page import BasePage


# page_url = https://www.wildberries.ru/
class WildberriesPage(BasePage):
    scheme = "https"
    domain = "www.wildberries.ru"
    path = ""

    def __init__(self, driver: Chrome):
        super().__init__(driver)
