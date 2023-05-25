import random
import time

import openpyxl
import pytest
import requests
from requests.exceptions import JSONDecodeError
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import LKDetailsPage, MainPage, SearchResultsPage
from parser_project import project_settings
from . import models


if project_settings.PRICE_POSITIONS:
    from selenium.webdriver import Chrome, ChromeOptions
else:
    from seleniumwire.webdriver import Chrome, ChromeOptions

City = dict[str, str]
Item = dict[str, str | list[str]]


class WildberriesParser:
    """Отвечает за весь процесс парсинга."""

    driver: Chrome
    _proxies: dict = None

    def get_proxy(self) -> str:
        if self._proxies is None:
            limit = 100
            url = f"https://proxylist.geonode.com/api/proxy-list?limit={limit}" \
                  f"&page=1&sort_by=lastChecked&sort_type=desc&speed=fast&protocols=http"
            response = requests.get(url)
            self._proxies = response.json()["data"]
        proxy_number = random.randint(0, len(self._proxies) - 1)
        # noinspection HttpUrlsUsage
        return f"http://{self._proxies[proxy_number]['ip']}:{self._proxies[proxy_number]['port']}"

    @staticmethod
    # для более точно работы нужны широта и долгота
    def get_geo(address: str) -> tuple[str, str]:
        url = f"https://user-geo-data.wildberries.ru/get-geo-info?currency=RUB&locale=ru&address={address}"
        response = requests.get(url)
        data = response.json()["xinfo"].split('&')
        dest = data[2].split('=')[-1]
        regions = data[3].split('=')[-1]
        return dest, regions

    def setup_method(self):
        selenium_wire_options = {
            "proxy": {
                # "http": self.get_proxy()
            }
        }

        options = ChromeOptions()
        # этот параметр тоже нужен, так как в режиме headless с некоторыми элементами нельзя взаимодействовать
        options.add_argument("--disable-blink-features=AutomationControlled")
        if project_settings.PRICE_POSITIONS:
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        if project_settings.PARSE_PRICES:
            self.driver = Chrome(options = options, service = service, seleniumwire_options = selenium_wire_options)
        else:
            self.driver = Chrome(options = options, service = service)

    def teardown_method(self):
        self.driver.quit()

    # метод не используется, но оставлен до худших времен
    def find_position_on_page(
            self,
            page_number: int,
            items_number: int,
            vendor_code: int,
            keyword: models.Keyword
    ) -> int:
        """Находит позицию товара на конкретной странице подобно пользователю."""

        search_results_page = SearchResultsPage(self.driver, page_number, keyword.value)
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
            search_results_page.scroll_down(50)
            search_results_page.items.reset()
        return position

    @staticmethod
    def find_position(city_dict: City, keyword: models.Keyword) -> models.Position:
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
                try_number = 0
                try_success = False
                while try_number < 3 and not try_success:
                    try_number += 1
                    try:
                        page_vendor_codes = [x["id"] for x in response.json()["data"]["products"]]
                        try_success = True
                    except JSONDecodeError:
                        # еще одна попытка
                        time.sleep(1)
                        if not try_success and try_number >= project_settings.ATTEMPT_NUMBER:
                            position = None
                else:
                    # noinspection PyUnboundLocalVariable
                    if keyword.item.vendor_code in page_vendor_codes:
                        position += page_vendor_codes.index(keyword.item.vendor_code) + 1
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

    @property
    def position_parser_item_dicts(self) -> list[dict[str, str | int]]:
        book = openpyxl.load_workbook(project_settings.POSITION_PARSER_DATA_PATH)
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

    @pytest.mark.skipif(project_settings.PARSE_PRICES, reason = "parse only prices")
    @pytest.mark.parametrize("city_dict", project_settings.CITIES)
    def run_position_parsing(self, city_dict: City) -> None:
        main_page = MainPage(self.driver)
        main_page.open()
        address = main_page.set_city(city_dict["name"])
        dest, regions = self.get_geo(address)
        city_dict["dest"] = dest
        city_dict["regions"] = regions
        for keyword in self.position_parser_keywords:
            position = self.find_position(city_dict, keyword)
            position.save()

    def parse_price(self, vendor_code: int, spp: int, city_dict: City) -> tuple[float, float, int]:
        proxies = {
            "http": self.get_proxy()
        }
        url = f"https://card.wb.ru/cards/detail?appType=1&curr=rub&dest={city_dict['dest']}" \
              f"&regions={city_dict['regions']}&spp={spp}&nm={vendor_code}"
        response = requests.get(url, proxies = proxies)
        data = response.json()["data"]["products"][0]["extended"]
        price = int(data["basicPriceU"]) / 100
        final_price = int(data["clientPriceU"]) / 100
        personal_sale = int(data["clientSale"])
        return price, final_price, personal_sale

    @property
    def price_parser_items(self) -> list[models.Item]:
        book = openpyxl.load_workbook(project_settings.PRICE_PARSER_DATA_PATH)
        sheet = book.active
        items = []
        row = 2
        while sheet.cell(row, 1).value:
            items.append(
                models.Item.objects.update_or_create(
                    vendor_code = sheet.cell(row, 1).value,
                    defaults = {"name": sheet.cell(row, 2).value}
                )[0]
            )
            row += 1
        return items

    @pytest.mark.skipif(project_settings.PRICE_POSITIONS, reason = "parse only positions")
    def run_price_parsing(self) -> None:
        main_page = MainPage(self.driver)
        main_page.open()
        main_page.authorize_manually()
        lk_details_page = LKDetailsPage(self.driver)
        lk_details_page.open()
        personal_sale = int(lk_details_page.personal_sale.text[:-1])
        city_dict = project_settings.CITIES[0]
        for item in self.price_parser_items:
            price, final_price, personal_sale = self.parse_price(item.vendor_code, personal_sale, city_dict)
            price = models.Price(
                item = item,
                price = price,
                final_price = final_price,
                personal_sale = personal_sale,
            )
            price.save()
