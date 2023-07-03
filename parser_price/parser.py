import openpyxl
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome, ChromeOptions, Remote

from core import parser as parser_core
from pages import ItemPage
from . import models


class ParserPrice(parser_core.ParserCore):
    log_in_driver: Chrome

    def setup_method(self):
        super().setup_method()
        self.log_in_driver = self.connect_log_in_driver()

    def connect_log_in_driver(self) -> Remote:
        options = ChromeOptions()
        options.add_argument("--headless")
        driver = Remote(self.settings.secrets.wildberries_log_in_driver.url, options = options)
        driver.close()
        driver.session_id = self.settings.secrets.wildberries_log_in_driver.session_id
        return driver

    def parse_price(self, item: models.Item) -> tuple[float, float, int | None, int]:
        page = ItemPage(self.driver, self.settings, item.vendor_code)
        page.open()
        page.transfer_cookies(self.log_in_driver)

        try:
            page.sold_out.init_if_necessary()
        except TimeoutException:
            page.price_block.open()
            price = float("".join(page.price_block.price.text.split()[:-1]))
            try:
                final_price = float("".join(page.price_block.final_price.text.split()[:-1]))
                personal_sale = int(page.price_block.personal_sale.text.split()[-1][:-1])
            except TimeoutException:
                final_price = float("".join(page.price_block.price.text.split()[:-1]))
                personal_sale = None
        else:
            price = None
            final_price = None
            personal_sale = None

        reviews_amount = int("".join([x for x in page.review_amount.text.split()[:-1]]))

        return price, final_price, personal_sale, reviews_amount

    @classmethod
    def get_price_parser_items(cls) -> list[models.Item]:
        book = openpyxl.load_workbook(cls.settings.PRICE_PARSER_DATA_PATH)
        sheet = book.active
        items = []
        row = 2
        while sheet.cell(row, 1).value:
            category = models.Category.objects.get_or_create(name = sheet.cell(row, 3).value)

            items.append(
                models.Item.objects.update_or_create(
                    vendor_code = sheet.cell(row, 1).value,
                    defaults = {"name_price": sheet.cell(row, 2).value, "category": category}
                )[0]
            )
            row += 1
        return items

    def run(self) -> None:
        for item in self.get_price_parser_items():
            price, final_price, personal_sale, reviews_amount = self.parse_price(item)
            price = models.Price(
                item = item,
                price = price,
                final_price = final_price,
                personal_sale = personal_sale,
                reviews_amount = reviews_amount
            )
            price.save()
