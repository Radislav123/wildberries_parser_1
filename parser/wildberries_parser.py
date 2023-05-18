import pytest
import requests
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

    def setup_method(self):
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        self.driver = Chrome(options = options, service = service)
        self.secrets = SecretKeeper()

    def teardown_method(self):
        self.driver.quit()

    def find_position_on_page(self, items_number: int, vendor_code: int, keyword: str) -> int:
        """Находит позицию товара на конкретной странице."""

        search_results_page = SearchResultsPage(self.driver, keyword)
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

    def find_position(self, keyword: str, city: City, product: Item) -> None | int:
        """Находит позицию товара в выдаче поиска по ключевому слову среди всех страниц."""

        try:
            page = 1
            position = 0
            while page:
                # noinspection SpellCheckingInspection
                url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&curr=rub&dest={city['dest']}" \
                      f"&page={page}&query={keyword}&regions={city['regions']}&resultset=catalog&sort=popular" \
                      f"&spp={city['spp']}&suppressSpellcheck=false"
                response = requests.get(url)
                page_vendor_codes = [x["id"] for x in response.json()["data"]["products"]]
                if int(product["vendor_code"]) in page_vendor_codes:
                    position += self.find_position_on_page(len(page_vendor_codes), int(product["vendor_code"]), keyword)
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
        return position

    def parse_positions(self, city: dict[str, str | list[str]]) -> list[models.Item]:
        items = []
        for item in project_settings.ITEMS:
            for keyword in item["keywords"]:
                items.append(
                    models.Item(
                        vendor_code = item["vendor_code"],
                        position = self.find_position(keyword, city, item)
                    )
                )
        return items

    @staticmethod
    def parse_other_data(vendor_code: int, city: dict[str, str]) -> tuple[int, float, float]:
        url = f"https://card.wb.ru/cards/detail?appType=1&curr=rub&dest={city['dest']}" \
              f"&regions={city['regions']}&spp={city['spp']}&nm={vendor_code}"
        response = requests.get(url)
        data = response.json()["data"]["products"][0]["extended"]
        personal_sale = int(data["clientSale"])
        cost_before_personal_sale = int(data["basicPriceU"]) / 100
        cost_final = int(data["clientPriceU"]) / 100
        return personal_sale, cost_before_personal_sale, cost_final

    # не использовать эту фикстуру - с ней не сохраняются объекты в БД
    # @pytest.mark.django_db
    @pytest.mark.parametrize("city", project_settings.CITIES)
    def run(self,  city: dict[str, str | list[str]]) -> None:
        main_page = MainPage(self.driver)
        main_page.authorize_and_open(self.secrets.wildberries_auth)
        items = self.parse_positions(city)
        for item in items:
            item.personal_sale, item.cost_before_personal_sale, item.cost_final = self.parse_other_data(
                item.vendor_code,
                city
            )
            item.save()
