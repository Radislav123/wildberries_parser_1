import json
import time

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

from pages import LogInPage
from parser_price.management.commands import parser_price_command
import pathlib


class Command(parser_price_command.ParserPriceCommand):
    help = "Открывает окно авторизации Wildberries для парсера цен"

    @staticmethod
    def get_authorization_driver() -> Chrome:
        options = ChromeOptions()

        options.add_argument("--no-sandbox")
        cache_manager = DriverCacheManager(root_dir = pathlib.Path.cwd())
        driver_manager = ChromeDriverManager(cache_manager = cache_manager).install()
        service = Service(executable_path = driver_manager)

        driver = Chrome(options = options, service = service)
        driver.maximize_window()
        return driver

    def write_driver_info(self, driver: Chrome) -> None:
        with open(self.settings.WILDBERRIES_LOG_IN_DRIVER_DATA_PATH, 'w') as file:
            # noinspection PyProtectedMember
            json.dump({"url": driver.command_executor._url, "session_id": driver.session_id}, file, indent = 2)

    def handle(self, *args, **options):
        driver = self.get_authorization_driver()
        login_page = LogInPage.create_without_parser(driver)
        login_page.open()
        self.write_driver_info(driver)
        while True:
            time.sleep(100)
