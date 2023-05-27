import random
import time

import openpyxl
import pytest
import requests
from requests.exceptions import JSONDecodeError
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

from pages import ItemPage, MainPage, SearchResultsPage
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
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities["goog:loggingPrefs"] = {"browser": "ALL"}
        parameters = {
            "options": options,
            "service": service,
            "desired_capabilities": desired_capabilities
        }

        if project_settings.PARSE_PRICES:
            parameters["seleniumwire_options"] = selenium_wire_options
        self.driver = Chrome(**parameters)
        self.driver.maximize_window()

    def teardown_method(self):
        self.driver.quit()

    # не используется, но оставлен
    def find_position_on_page(self, page_number: int, items_number: int, keyword: models.Keyword) -> int:
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
                if item_id == keyword.item.vendor_code:
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
                while try_number < project_settings.ATTEMPT_NUMBER and not try_success:
                    try_number += 1
                    try:
                        page_vendor_codes = [x["id"] for x in response.json()["data"]["products"]]
                        try_success = True
                    except JSONDecodeError:
                        if not try_success and try_number >= project_settings.ATTEMPT_NUMBER:
                            position = None
                            page = None
                            break
                        else:
                            # еще одна попытка
                            time.sleep(1)
                else:
                    # noinspection PyUnboundLocalVariable
                    if keyword.item.vendor_code in page_vendor_codes:
                        position += page_vendor_codes.index(keyword.item.vendor_code) + 1
                        break
                    else:
                        position += len(page_vendor_codes)
                    page += 1
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
        dest, regions = main_page.set_city(city_dict["name"])
        city_dict["dest"] = dest
        city_dict["regions"] = regions
        for keyword in self.position_parser_keywords:
            position = self.find_position(city_dict, keyword)
            position.save()

    def parse_price(self, item: models.Item) -> tuple[float, float, int]:
        page = ItemPage(self.driver, item.vendor_code)
        page.open()
        page.price_block.open()

        price = float("".join(page.price_block.price.text.split()[:-1]))
        final_price = float("".join(page.price_block.final_price.text.split()[:-1]))
        personal_sale = int(page.price_block.personal_sale.text.split()[-1][:-1])
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
        for item in self.price_parser_items:
            price, final_price, personal_sale = self.parse_price(item)
            price = models.Price(
                item = item,
                price = price,
                final_price = final_price,
                personal_sale = personal_sale,
            )
            price.save()
