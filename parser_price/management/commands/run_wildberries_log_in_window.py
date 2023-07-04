import json
import time

from django.core.management.base import BaseCommand
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import LogInPage
from parser_price.settings import Settings


class Command(BaseCommand):
    help = "Открывает окно авторизации Wildberries для парсера цен"

    @staticmethod
    def get_authorization_driver() -> Chrome:
        options = ChromeOptions()

        options.add_argument("--no-sandbox")
        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        driver = Chrome(options = options, service = service)
        driver.maximize_window()
        return driver

    @staticmethod
    def write_driver_info(driver: Chrome, settings: Settings) -> None:
        with open(settings.WILDBERRIES_LOG_IN_DRIVER_DATA_PATH, 'w') as file:
            # noinspection PyProtectedMember
            json.dump({"url": driver.command_executor._url, "session_id": driver.session_id}, file, indent = 2)

    def handle(self, *args, **options):
        settings = Settings()
        driver = self.get_authorization_driver()
        login_page = LogInPage()
        login_page.open()
        self.write_driver_info(driver, settings)
        while True:
            time.sleep(100)
