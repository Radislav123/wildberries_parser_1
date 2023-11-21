from typing import Any

import openpyxl
from selenium.webdriver import Chrome

from bot_telegram import bot
from core import models as core_models, parser as parser_core
from core.service import parsing
from . import models, settings


class Parser(parser_core.Parser):
    settings = settings.Settings()
    log_in_driver: Chrome
    bot_telegram = bot.Bot()
    parsing_type = "price"

    def parse_items(
            self,
            items: list[models.Item],
            dest: str
    ) -> tuple[list[models.Price], dict[models.Item, Exception]]:
        items_dict = {x.vendor_code: x for x in items}
        prices, errors = parsing.parse_prices(list(items_dict), dest)
        errors = {items_dict[vendor_code]: error for vendor_code, error in errors.items()}
        price_objects = []
        for vendor_code, price in prices.items():
            price_object = models.Price(
                item = items_dict[vendor_code],
                parsing = self.parsing,
                reviews_amount = price["reviews_amount"],
                price = price["price"],
                final_price = price["final_price"],
                personal_sale = price["personal_sale"]
            )
            price_objects.append(price_object)
            items_dict[vendor_code].category = models.Category.objects.get_or_create(name = price["category_name"])[0]

        models.Price.objects.bulk_create(price_objects)
        models.Item.objects.bulk_update(items_dict.values(), ["category"])

        return price_objects, errors

    @classmethod
    def get_price_parser_item_dicts(cls) -> list[dict[str, Any]]:
        book = openpyxl.load_workbook(cls.settings.PARSER_PRICE_DATA_PATH)
        sheet = book.active
        items = {}
        row = 2
        while sheet.cell(row, 1).value:
            item = {
                "vendor_code": sheet.cell(row, 1).value,
                "name": sheet.cell(row, 2).value
            }
            items[item["vendor_code"]] = item
            row += 1
        return list(items.values())

    @classmethod
    def get_price_parser_items(cls) -> list[models.Item]:
        item_dicts = cls.get_price_parser_item_dicts()
        items = []

        # todo: переписать с использованием bulk_create
        # https://stackoverflow.com/a/74189912/13186004
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
                 if x.id % self.settings.PYTEST_XDIST_WORKER_COUNT == division_remainder]
        self.run(items, True)

    def run_other(self, division_remainder: int) -> None:
        items = [x for x in models.Item.objects.exclude(user = core_models.ParserUser.get_customer())
                 if x.id % self.settings.PYTEST_XDIST_WORKER_COUNT == division_remainder]
        self.run(items, False)

    def run(self, items: list[models.Item], prepare_table: bool) -> None:
        city_dict = self.settings.MOSCOW_CITY_DICT
        dest = city_dict["dest"]
        prices, errors = self.parse_items(items, dest)
        self.parsing.not_parsed_items = errors

        notifications = models.Price.get_notifications(prices)
        self.bot_telegram.notify(notifications)

        if prepare_table:
            models.PreparedPrice.prepare([x for x in items if x not in errors])
