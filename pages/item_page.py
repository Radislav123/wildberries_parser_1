from selenium.webdriver import Chrome

from elements import ExtendedWebElement
from pages.wildberries_page import WildberriesPage


# page_url = https://www.wildberries.ru/catalog/110565259/detail.aspx
class ItemPage(WildberriesPage):
    def __init__(self, driver: Chrome) -> None:
        super().__init__(driver)
        self.vendor_code = ExtendedWebElement(self, '//span[@id = "productNmId"]')
