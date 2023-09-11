from typing import Any

import openpyxl
import requests
from selenium.webdriver import Chrome

from bot_telegram import bot
from core import models as core_models, parser as parser_core
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
                if "basicPriceU" not in item_dict["extended"]:
                    price = None
                    final_price = None
                    personal_sale = None
                else:
                    price = item_dict["extended"]["basicPriceU"]
                    final_price = item_dict["salePriceU"]
                    if price == final_price:
                        personal_sale = None
                    else:
                        personal_sale = int(item_dict["extended"]["clientSale"])
                    price = int(price) / 100
                    final_price = int(final_price) / 100

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

                part = item.vendor_code // 1000
                vol = part // 100
                for basket in range(1, 99):
                    category_url = (f"https://basket-{str(basket).rjust(2, '0')}.wb.ru/vol{vol}"
                                    f"/part{part}/{item.vendor_code}/info/ru/card.json")
                    category_response = requests.get(category_url)
                    if category_response.status_code == 200:
                        category_name = category_response.json()["subj_name"]
                        item.category = models.Category.objects.get_or_create(name = category_name)[0]
                        break
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
        city_dict = [x for x in self.settings.CITIES if x["label"].lower() == "moscow"][0]
        main_page = MainPage(self)
        main_page.open()
        dest, regions = main_page.set_city(city_dict)
        prices, errors = self.parse_items(items, dest, regions)
        self.parsing.not_parsed_items = errors

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
