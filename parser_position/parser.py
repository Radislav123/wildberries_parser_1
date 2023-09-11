import time

import openpyxl
import requests
from requests.exceptions import JSONDecodeError

from core import models as core_models, parser as parser_core
from pages import MainPage, SearchResultsPage
from . import models, settings


City = dict[str, str]


class Parser(parser_core.Parser):
    settings = settings.Settings()
    parsing_type = "position"

    # не используется, но оставлен
    def find_position_on_page(self, page_number: int, items_number: int, keyword: models.Keyword) -> int:
        """Находит позицию товара на конкретной странице подобно пользователю."""

        search_results_page = SearchResultsPage(self, page_number, keyword.value)
        search_results_page.open()
        checked_items = 0
        found = False
        # None возвращаться не должен, так как этот товар точно есть на странице
        position = None

        while not found and items_number > len(search_results_page.items):
            for number, item in enumerate(search_results_page.items[checked_items:], checked_items + 1):
                checked_items += 1
                # ожидание прогрузки
                item.init(item.WaitCondition.VISIBLE)
                item_id = int(item.get_attribute("data-nm-id"))
                if item_id == keyword.item.vendor_code:
                    position = number
                    found = True
                    break
            search_results_page.scroll_down(50)
            search_results_page.items.reset()
        return position

    def find_position(self, city_dict: City, keyword: models.Keyword) -> models.Position:
        """Находит позицию товара в выдаче поиска по ключевому слову среди всех страниц."""

        try:
            page = 1
            position = None
            page_capacities = []
            while page:
                # noinspection SpellCheckingInspection
                url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&curr=rub" \
                      f"&dest={city_dict['dest']}&page={page}&query={keyword.value}&regions={city_dict['regions']}" \
                      f"&resultset=catalog&sort=popular&spp=0&suppressSpellcheck=false"
                response = requests.get(url)
                try_number = 0
                try_success = False
                while try_number < self.settings.REQUEST_PAGE_ITEMS_ATTEMPTS_AMOUNT and not try_success:
                    try_number += 1
                    try:
                        page_vendor_codes = [x["id"] for x in response.json()["data"]["products"]]
                        try_success = True
                    except JSONDecodeError:
                        if not try_success and try_number >= self.settings.REQUEST_PAGE_ITEMS_ATTEMPTS_AMOUNT:
                            page = None
                            break
                        else:
                            # еще одна попытка
                            time.sleep(1)
                else:
                    # noinspection PyUnboundLocalVariable
                    page_capacities.append(len(page_vendor_codes))
                    if keyword.item.vendor_code in page_vendor_codes:
                        position = page_vendor_codes.index(keyword.item.vendor_code) + 1
                        break
                    page += 1
        except KeyError as error:
            if "data" in error.args:
                # если возвращаемая позиция == None => товар не был найден по данному ключевому слову
                page_capacities = None
                page = None
                position = None
            else:
                raise error
        return models.Position(
            keyword = keyword,
            parsing = self.parsing,
            city = city_dict["name"],
            page_capacities = page_capacities,
            page = page,
            value = position
        )

    @classmethod
    def get_position_parser_item_dicts(cls) -> list[dict[str, str | int]]:
        book = openpyxl.load_workbook(cls.settings.PARSER_POSITION_DATA_PATH)
        sheet = book.active
        items = []
        row = 2
        while sheet.cell(row, 1).value:
            items.append(
                {
                    "vendor_code": int(sheet.cell(row, 1).value),
                    "name": sheet.cell(row, 2).value,
                    "keyword": sheet.cell(row, 3).value
                }
            )
            row += 1
        return items

    @classmethod
    def get_position_parser_keywords(cls) -> list[models.Keyword]:
        item_dicts = cls.get_position_parser_item_dicts()
        # создание отсутствующих товаров в БД
        items = {
            x["vendor_code"]: models.Item.objects.get_or_create(
                vendor_code = x["vendor_code"],
                user = core_models.ParserUser.get_customer()
            )[0] for x in item_dicts
        }

        keywords = [
            models.Keyword.objects.update_or_create(
                item = items[x["vendor_code"]],
                item__user = core_models.ParserUser.get_customer(),
                value = x["keyword"],
                defaults = {"item_name": x["name"]}
            )[0] for x in item_dicts
        ]
        return keywords

    # todo: добавить сохранение ошибок и продолжение парсинга при ошибке по образу парсера цен
    def run_customer(self, city_dict: City) -> None:
        main_page = MainPage(self)
        main_page.open()
        dest, regions = main_page.set_city(city_dict)
        city_dict["dest"] = dest
        city_dict["regions"] = regions
        keywords = self.get_position_parser_keywords()
        for keyword in keywords:
            position = self.find_position(city_dict, keyword)
            position.save()

        models.PreparedPosition.prepare(keywords, city_dict["name"])

    def run_other(self, city_dict: City) -> None:
        raise NotImplementedError()
