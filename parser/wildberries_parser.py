import pytest
import requests
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import MainPage, SearchResultsPage
from parser_project import project_settings


City = dict[str, str]
Product = dict[str, str | list[str]]


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
                item_id = int(item.get_attribute("data-nm-id"))
                if item_id == vendor_code:
                    position = number
                    found = True
                    break
            search_results_page.scroll_down(1000)
            search_results_page.items.initialized = False
        return position

    def find_position(self, keyword: str, city: City, product: Product) -> int:
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
                # если возвращаемая позиция == -1 => товар не был найден по данному ключевому слову
                position = -1
            else:
                raise error
        return position

    @pytest.mark.parametrize("city", project_settings.CITIES)
    def run(self, city: dict[str, str | list[str]]):
        main_page = MainPage(self.driver)
        main_page.authorize_and_open(self.secrets.wildberries_auth)
        # todo: return line
        # main_page.set_city(city)

        for product in project_settings.PRODUCTS:
            for keyword in product["keywords"]:
                # todo: rewrite it
                position = self.find_position(keyword, city, product)
                print("----------------------------")
                print(position)
                print("----------------------------")
