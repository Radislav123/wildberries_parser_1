import openpyxl
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome, ChromeOptions, Remote

from core import parser as parser_core, models as core_models
from pages import ItemPage
from . import models, settings


class ParserPrice(parser_core.ParserCore):
    settings = settings.Settings()
    log_in_driver: Chrome

    def setup_method(self):
        super().setup_method()
        self.log_in_driver = self.connect_log_in_driver()

    def teardown_method(self):
        super().teardown_method()
        models.PreparedPrice.prepare()

    def connect_log_in_driver(self) -> Remote:
        options = ChromeOptions()
        options.add_argument("--headless")
        driver = Remote(self.settings.secrets.wildberries_log_in_driver.url, options = options)
        driver.close()
        driver.session_id = self.settings.secrets.wildberries_log_in_driver.session_id
        return driver

    def parse_price(self, item: models.Item) -> tuple[int, float, float, int | None]:
        page = ItemPage(self, item.vendor_code)
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

        return reviews_amount, price, final_price, personal_sale

    @classmethod
    def get_price_parser_items(cls, user: core_models.ParserUser) -> list[models.Item]:
        book = openpyxl.load_workbook(cls.settings.PARSER_PRICE_DATA_PATH)
        sheet = book.active
        items = []
        row = 2
        while sheet.cell(row, 1).value:
            category_name = sheet.cell(row, 3).value
            if category_name is not None:
                category = models.Category.objects.get_or_create(name = category_name)[0]
            else:
                category = None

            items.append(
                models.Item.objects.update_or_create(
                    vendor_code = sheet.cell(row, 1).value,
                    user = user,
                    defaults = {"name": sheet.cell(row, 2).value, "category": category}
                )[0]
            )
            row += 1
        return items

    def run(self) -> None:
        for item in self.get_price_parser_items(self.user):
            reviews_amount, price, final_price, personal_sale = self.parse_price(item)
            price = models.Price(
                item = item,
                parsing = self.parsing,
                reviews_amount = reviews_amount,
                price = price,
                final_price = final_price,
                personal_sale = personal_sale
            )
            price.save()
