from selenium.webdriver import ActionChains, Chrome

from web_elements import ExtendedWebElement
from .wildberries_base_page import WildberriesPage


# page_url = https://www.wildberries.ru/catalog/110565259/detail.aspx
class ItemPage(WildberriesPage):
    class PriceBlock(ExtendedWebElement):
        def __init__(self, page: "ItemPage", xpath: str) -> None:
            super().__init__(page, xpath)
            self.price = ExtendedWebElement(self.page, '//div[@class = "discount-tooltipster-content"]/p[2]/span[2]')
            self.final_price = ExtendedWebElement(
                self.page, '//div[@class = "discount-tooltipster-content"]/p[3]/span[2]'
            )
            self.personal_sale = ExtendedWebElement(
                self.page, '//div[@class = "discount-tooltipster-content"]/p[3]/span[1]'
            )

        # не работает, так как авторизация не полная
        def open(self) -> None:
            self.init(self.WaitCondition.VISIBLE)
            action = ActionChains(self.driver)
            action.move_to_element(self.selenium_element).perform()
            self.click()

    def __init__(self, driver: Chrome, vendor_code: int) -> None:
        super().__init__(driver)
        self.vendor_code = vendor_code
        self.path = f"catalog/{self.vendor_code}/detail.aspx"
        self.vendor_code = ExtendedWebElement(self, '//span[@id = "productNmId"]')
        self.price_block = self.PriceBlock(self, '//del[contains(@class, "price-block")]')
