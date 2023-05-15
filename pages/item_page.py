from selenium.webdriver import Chrome

from elements import ExtendedWebElement
from pages import BasePage


# page_url = https://www.wildberries.ru/catalog/110565259/detail.aspx
class ItemPage(BasePage):
    def __init__(self, driver: Chrome, url: str):
        super().__init__(driver, url)
        self.vendor_code = ExtendedWebElement(self, '//span[@id = "productNmId"]')

    def open(self):
        self.driver.get(self.url)
