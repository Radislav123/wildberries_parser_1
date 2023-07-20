from typing import Any

import openpyxl
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome, ChromeOptions, Remote

from bot_telegram import bot
from core import models as core_models, parser as parser_core
from pages import ItemPage
from . import models, settings


class Parser(parser_core.Parser):
    settings = settings.Settings()
    log_in_driver: Chrome
    bot_telegram = bot.Bot()

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

    @staticmethod
    def update_item_name_site(item: models.Item, page: ItemPage) -> None:
        item.name_site = page.item_full_name
        item.save()

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
        self.update_item_name_site(item, page)

        return reviews_amount, price, final_price, personal_sale

    @classmethod
    def get_price_parser_item_dicts(cls) -> list[dict[str, Any]]:
        book = openpyxl.load_workbook(cls.settings.PARSER_PRICE_DATA_PATH)
        sheet = book.active
        item_dicts = []
        row = 2
        while sheet.cell(row, 1).value:
            item_dicts.append(
                {
                    "vendor_code": sheet.cell(row, 1).value,
                    "name": sheet.cell(row, 2).value,
                    "category_name": sheet.cell(row, 3).value
                }
            )
            row += 1
        return item_dicts

    @classmethod
    def get_price_parser_items(cls, user: core_models.ParserUser) -> list[models.Item]:
        item_dicts = cls.get_price_parser_item_dicts()
        items = []

        for item_dict in item_dicts:
            if item_dict["category_name"] is not None:
                category = models.Category.objects.get_or_create(name = item_dict["category_name"])[0]
            else:
                category = None

            items.append(
                models.Item.objects.update_or_create(
                    vendor_code = item_dict["vendor_code"],
                    user = user,
                    defaults = {"name": item_dict["name"], "category": category}
                )[0]
            )
        return items

    def run(self, vendor_codes: list[int]) -> None:
        items = models.Item.objects.filter(vendor_code__in = vendor_codes, user = self.user)
        prices = []
        for item in items:
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
            prices.append(price)

        changed_prices = models.Price.get_changed_prices(prices)
        self.bot_telegram.notify_prices_changed(changed_prices)

        models.PreparedPrice.prepare(self.user, items)
