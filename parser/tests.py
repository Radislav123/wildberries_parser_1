from django.test import TestCase
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import ItemPage


def parse(page: ItemPage):
    page.open()


def get_browser() -> Chrome:
    options = ChromeOptions()
    options.add_argument("--start-maximized")

    driver_manager = ChromeDriverManager(path = "").install()
    service = Service(executable_path = driver_manager)

    browser = Chrome(options = options, service = service)
    return browser


class Test(TestCase):
    def test(self):
        browser_driver = get_browser()
        item_page = ItemPage(browser_driver, "https://www.wildberries.ru/catalog/110565259/detail.aspx")
        parse(item_page)
        print(item_page.vendor_code.text)
