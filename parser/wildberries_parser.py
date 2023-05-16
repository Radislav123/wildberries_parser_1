import time

import pytest
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import ItemPage, MainPage
from parser_project import project_settings


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

    @pytest.mark.parametrize("city", project_settings.CITIES_TO_PARSE)
    def run(self, city):
        main_page = MainPage(self.driver)
        main_page.authorize_and_open(self.secrets.wildberries_auth)
        main_page.set_city(city)
        time.sleep(1)

    def parse_old(self):
        item_page = ItemPage(self.driver)
        item_page.open()
        print(item_page.vendor_code.text)
