from selenium.webdriver import Chrome

from web_elements import ExtendedWebElement
from .wildberries_base_page import WildberriesPage


# page_url = https://www.wildberries.ru/catalog/110565259/detail.aspx
class ItemPage(WildberriesPage):
    def __init__(self, driver: Chrome, vendor_code: int) -> None:
        super().__init__(driver)
        self.vendor_code = vendor_code
        self.path = f"catalog/{self.vendor_code}/detail.aspx"
        self.vendor_code = ExtendedWebElement(self, '//span[@id = "productNmId"]')
