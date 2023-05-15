import time

from django.test import TestCase
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import ItemPage, MainPage


class Test(TestCase):
    """Отвечает за весь процесс парсинга."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        options = ChromeOptions()
        options.add_argument("--start-maximized")

        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        self.driver = Chrome(options = options, service = service)

    def test(self):
        main_page = MainPage(self.driver)
        main_page.open()
        # todo: вынести выбор города в параметры
        main_page.set_city("Казань")
        time.sleep(5)

    def parse_old(self):
        item_page = ItemPage(self.driver)
        item_page.open()
        print(item_page.vendor_code.text)
