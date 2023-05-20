import time

import openpyxl
import pytest
import requests
from requests.exceptions import JSONDecodeError
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import MainPage, SearchResultsPage
from parser_project import project_settings
from . import models


City = dict[str, str]
Item = dict[str, str | list[str]]


class SecretKeeper:
    class CredentialsOnly:
        def __init__(self, login: str, password: str) -> None:
            self.login = login
            self.password = password

        def __str__(self) -> str:
            return f"login: {self.login}\npassword: {self.password}"

    class Cookie:
        def __init__(self, name: str, value: str) -> None:
            self.name = name
            self.value = value

        def __str__(self) -> str:
            return f"name: {self.name}\nvalue: {self.value}"

        def to_dict(self) -> dict[str, str]:
            return {"name": self.name, "value": self.value}

    def __init__(self) -> None:
        self.wildberries_auth = self.Cookie(*self.read_secret(project_settings.WILDBERRIES_AUTH_COOKIE_PATH))

    @staticmethod
    def read_secret(path: str) -> list[str]:
        with open(path, 'r') as file:
            data = [x.strip() for x in file]
        return data


class WildberriesParser:
    """Отвечает за весь процесс парсинга."""

    driver: Chrome
    secrets: SecretKeeper

    def setup_selenium(self):
        options = ChromeOptions()
        # этот параметр тоже нужен, так как в режиме headless с некоторыми элементами нельзя взаимодействовать
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        self.driver = Chrome(options = options, service = service)
        self.secrets = SecretKeeper()

    def teardown_selenium(self):
        self.driver.quit()

    def find_position_on_page(self, items_number: int, vendor_code: int, keyword: models.Keyword) -> int:
        """Находит позицию товара на конкретной странице."""

        search_results_page = SearchResultsPage(self.driver, keyword.value)
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
                if item_id == vendor_code:
                    position = number
                    found = True
                    break
            search_results_page.scroll_down(100)
            search_results_page.items.reset()
        return position

    def find_position(self, city_dict: City, keyword: models.Keyword) -> models.Position:
        """Находит позицию товара в выдаче поиска по ключевому слову среди всех страниц."""

        try:
            page = 1
            position = 0
            while page:
                # noinspection SpellCheckingInspection
                url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&curr=rub" \
                      f"&dest={city_dict['dest']}&page={page}&query={keyword.value}&regions={city_dict['regions']}" \
                      f"&resultset=catalog&sort=popular&spp=0&suppressSpellcheck=false"
                response = requests.get(url)
                try:
                    page_vendor_codes = [x["id"] for x in response.json()["data"]["products"]]
                except JSONDecodeError:
                    # еще одна попытка
                    time.sleep(1)
                    page_vendor_codes = [x["id"] for x in response.json()["data"]["products"]]
                if keyword.item.vendor_code in page_vendor_codes:
                    position += self.find_position_on_page(len(page_vendor_codes), keyword.item.vendor_code, keyword)
                    break
                else:
                    page += 1
                    position += len(page_vendor_codes)
        except KeyError as error:
            if "data" in error.args:
                # если возвращаемая позиция == None => товар не был найден по данному ключевому слову
                position = None
            else:
                raise error
        return models.Position(keyword = keyword, city = city_dict["name"], value = position)

    @staticmethod
    def parse_price(vendor_code: int, spp: int, city: City) -> tuple[float, float, int]:
        url = f"https://card.wb.ru/cards/detail?appType=1&curr=rub&dest={city['dest']}" \
              f"&regions={city['regions']}&spp={spp}&nm={vendor_code}"
        response = requests.get(url)
        data = response.json()["data"]["products"][0]["extended"]
        price = int(data["basicPriceU"]) / 100
        final_price = int(data["clientPriceU"]) / 100
        personal_sale = int(data["clientSale"])
        return price, final_price, personal_sale

    @property
    def position_parser_item_dicts(self) -> list[dict[str, str | int]]:
        book = openpyxl.load_workbook(project_settings.POSITION_PARSER_DATA_PATH)
        sheet = book.active
        items = []
        row = 2
        while sheet.cell(row, 1).value:
            items.append(
                {
                    "name": sheet.cell(row, 1).value,
                    "vendor_code": int(sheet.cell(row, 2).value),
                    "keyword": sheet.cell(row, 3).value
                }
            )
            row += 1
        return items

    @property
    def position_parser_keywords(self) -> list[models.Keyword]:
        item_dicts = self.position_parser_item_dicts
        # создание отсутствующих товаров в БД
        # noinspection PyStatementEffect
        [models.Item.objects.update_or_create(vendor_code = x["vendor_code"], defaults = {"name": x["name"]})[0]
         for x in item_dicts]

        keywords = [models.Keyword.objects.get_or_create(value = x["keyword"], item_id = x["vendor_code"])[0]
                    for x in item_dicts]
        return keywords

    # todo: заполнить cities.json
    @pytest.mark.skipif(project_settings.SKIP_POSITION_PARSING, reason = "parse only prices")
    @pytest.mark.parametrize("city_dict", project_settings.CITIES)
    def run_position_parsing(self, city_dict: City) -> None:
        self.setup_selenium()

        main_page = MainPage(self.driver)
        main_page.open()
        main_page.set_city(city_dict["name"])
        for keyword in self.position_parser_keywords:
            position = self.find_position(city_dict, keyword)
            position.save()

        self.teardown_selenium()

    @property
    def price_parser_items(self) -> list[models.Item]:
        book = openpyxl.load_workbook(project_settings.PRICE_PARSER_DATA_PATH)
        sheet = book.active
        items = []
        row = 2
        while sheet.cell(row, 1).value:
            items.append(models.Item.objects.get_or_create(vendor_code = sheet.cell(row, 1).value)[0])
            row += 1
        return items

    @pytest.mark.skipif(project_settings.SKIP_PRICE_PARSING, reason = "parse only positions")
    def run_price_parsing(self) -> None:
        for item in self.price_parser_items:
            # todo: брать спп из файла
            spp = 15
            price, final_price, personal_sale = self.parse_price(item.vendor_code, spp, project_settings.CITIES[0])
            price = models.Price(
                item = item,
                price = price,
                final_price = final_price,
                personal_sale = personal_sale,
            )
            price.save()
