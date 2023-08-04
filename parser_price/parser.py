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

    def parse_price(self, item: models.Item) -> models.Price:
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

        price = models.Price(
            item = item,
            parsing = self.parsing,
            reviews_amount = reviews_amount,
            price = price,
            final_price = final_price,
            personal_sale = personal_sale
        )

        item.category = models.Category.objects.get_or_create(name = page.category.text)[0]
        item.save()

        return price

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
                    "name": sheet.cell(row, 2).value
                }
            )
            row += 1
        return item_dicts

    @classmethod
    def get_price_parser_items(cls) -> list[models.Item]:
        item_dicts = cls.get_price_parser_item_dicts()
        items = []

        for item_dict in item_dicts:
            items.append(
                models.Item.objects.update_or_create(
                    vendor_code = item_dict["vendor_code"],
                    user = core_models.ParserUser.get_customer(),
                    defaults = {"name": item_dict["name"]}
                )[0]
            )
        return items

    def run_customer(self, division_remainder: int) -> None:
        items = [x for x in self.get_price_parser_items()
                 # todo: return line
                 # if x.id % self.settings.PYTEST_XDIST_WORKER_COUNT == division_remainder]
                 if x.vendor_code % self.settings.PYTEST_XDIST_WORKER_COUNT == division_remainder]
        self.run(items, True)

    def run_other(self, division_remainder: int) -> None:
        items = [x for x in models.Item.objects.exclude(user = core_models.ParserUser.get_customer())
                 # todo: return line
                 # if x.id % self.settings.PYTEST_XDIST_WORKER_COUNT == division_remainder]
                 if x.vendor_code % self.settings.PYTEST_XDIST_WORKER_COUNT == division_remainder]
        self.run(items, False)

    def run(self, items: list[models.Item], prepare_table: bool):
        self.parsing.not_parsed_items = {}
        prices = []
        for item in items:
            try:
                price = self.parse_price(item)
                price.save()
                prices.append(price)
            except TimeoutException as error:
                self.parsing.not_parsed_items[item] = error

        notifications = models.Price.get_notifications(prices)
        self.bot_telegram.notify(notifications)

        if prepare_table:
            models.PreparedPrice.prepare(items)
        if len(self.parsing.not_parsed_items) > 0:
            self.logger.info(f"Not parsed items: {self.parsing.not_parsed_items}")
            self.parsing.success = False
            self.parsing.save()

            exception = parser_core.UnsuccessfulParsing(*list(self.parsing.not_parsed_items.values()))
            raise exception from exception.args[-1]
        else:
            self.parsing.not_parsed_items = None
            self.parsing.success = True
            self.parsing.save()
