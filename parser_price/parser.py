from typing import Any

import openpyxl
import requests
from selenium.webdriver import Chrome

from bot_telegram import bot
from core import models as core_models, parser as parser_core, service
from pages import MainPage
from . import models, settings


class Parser(parser_core.Parser):
    settings = settings.Settings()
    log_in_driver: Chrome
    bot_telegram = bot.Bot()
    parsing_type = "price"

    def parse_items(
            self,
            items: list[models.Item],
            dest: str,
            regions: str
    ) -> tuple[list[models.Price], dict[models.Item, Exception]]:
        # если указать СПП меньше реальной, придут неверные данные, при СПП >= 100 данные не приходят
        request_personal_sale = 99
        url = (f"https://card.wb.ru/cards/detail?appType=1&curr=rub"
               f"&dest={dest}&regions={regions}&spp={request_personal_sale}"
               f"&nm={';'.join([str(x.vendor_code) for x in items])}")
        items_response = requests.get(url)

        item_dicts = {x["id"]: x for x in items_response.json()["data"]["products"]}
        price_objects = []
        errors = {}
        for item in items:
            try:
                item_dict: dict = item_dicts[item.vendor_code]
                price, final_price, personal_sale = service.get_price(item_dict)

                price_object = models.Price(
                    item = item,
                    parsing = self.parsing,
                    reviews_amount = int(item_dict["feedbacks"]),
                    price = price,
                    final_price = final_price,
                    personal_sale = personal_sale
                )
                price_object.save()
                price_objects.append(price_object)

                item.category = models.Category.objects.get_or_create(
                    name = service.get_category_name(item.vendor_code)
                )[0]
                item.name_site = f"{item_dict['brand']} / {item_dict['name']}"
                item.save()
            except Exception as error:
                errors[item] = error

        return price_objects, errors

    @classmethod
    def get_price_parser_item_dicts(cls) -> list[dict[str, Any]]:
        book = openpyxl.load_workbook(cls.settings.PARSER_PRICE_DATA_PATH)
        sheet = book.active
        item_dicts = []
        row = 2
        while sheet.cell(row, 1).value:
            item_dicts.append({"vendor_code": sheet.cell(row, 1).value, "name": sheet.cell(row, 2).value})
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
                 if x.id % self.settings.PYTEST_XDIST_WORKER_COUNT == division_remainder]
        self.run(items, True)

    def run_other(self, division_remainder: int) -> None:
        items = [x for x in models.Item.objects.exclude(user = core_models.ParserUser.get_customer())
                 if x.id % self.settings.PYTEST_XDIST_WORKER_COUNT == division_remainder]
        self.run(items, False)

    def run(self, items: list[models.Item], prepare_table: bool) -> None:
        city_dict = self.settings.MOSCOW_CITY_DICT
        main_page = MainPage(self)
        main_page.open()
        dest, regions = main_page.set_city(city_dict)
        prices, errors = self.parse_items(items, dest, regions)
        self.parsing.not_parsed_items = errors

        notifications = models.Price.get_notifications(prices)
        self.bot_telegram.notify(notifications)

        if prepare_table:
            models.PreparedPrice.prepare(items)
