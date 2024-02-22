from parsing_helper.web_elements import ExtendedWebElement
from selenium.common.exceptions import TimeoutException

from .wildberries_base_page import WildberriesPage


class OutdatedException(Exception):
    pass


# page_url = https://www.wildberries.ru/catalog/110565259/detail.aspx
class ItemPage(WildberriesPage):
    class PriceBlock(ExtendedWebElement):
        def __init__(self, page: "ItemPage", xpath: str) -> None:
            super().__init__(page, xpath)
            self.price = ExtendedWebElement(self.page, '//div[@class = "discount-tooltipster-content"]/p[2]/span[2]')
            self.final_price = ExtendedWebElement(
                self.page, '//div[@class = "discount-tooltipster-content"]/p[3]/span[2]'
            )
            self.personal_discount = ExtendedWebElement(
                self.page, '//div[@class = "discount-tooltipster-content"]/p[3]/span[1]'
            )
            raise OutdatedException()

        def open(self) -> None:
            self.init_if_necessary()
            js_script = f"""xPathResult = document.evaluate('{self.xpath}', document);
                        element = xPathResult.iterateNext();
                        const mouseoverEvent = new Event('mouseover');
                        element.dispatchEvent(mouseoverEvent);"""
            self.driver.execute_script(js_script)

    def __init__(self, parser, vendor_code: int) -> None:
        super().__init__(parser)
        self.vendor_code = vendor_code
        self.path = f"catalog/{self.vendor_code}/detail.aspx"
        # сейчас этого нет на странице, но код оставлен, чтобы не потерять способ решения связанных проблем (метод open)
        # self._price_block_outdated = self.PriceBlock(self, '//del')
        self.price = ExtendedWebElement(self, '(//ins[@class = "price-block__final-price"])[2]')
        self.sold_out = ExtendedWebElement(self, '//span[@class = "sold-out-product__text"]')
        self.review_amount = ExtendedWebElement(self, '//span[@class = "product-review__count-review"]')

        self.vendor_code = ExtendedWebElement(self, '//button[@id = "productNmId"]')
        self.item_header = ExtendedWebElement(self, '//div[@class = "product-page__header"]')
        self.item_brand = ExtendedWebElement(self, f"{self.item_header.xpath}/span")
        self.item_name = ExtendedWebElement(self, f"{self.item_header.xpath}/h1")
        self.category = ExtendedWebElement(self, '//span[contains(@data-link, "subjectName")]')

    def get_item_full_name(self) -> str:
        return f"{self.item_brand.text} / {self.item_name.text}"

    def get_price(self) -> float:
        return float("".join(self.price.text.split()[:-1]))

    def check_sold_out(self) -> bool:
        try:
            self.sold_out.init_if_necessary()
        except TimeoutException:
            sold_out = False
        else:
            sold_out = True
        finally:
            self.sold_out.reset()
        return sold_out
