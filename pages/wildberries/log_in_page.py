import json

from selenium.webdriver import Chrome, ChromeOptions, Remote
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from parser import settings
from web_elements import ExtendedWebElement, ExtendedWebElementCollection
from .events_page import EventsPage
from .wildberries_base_page import WildberriesPage


# page_url = https://www.wildberries.ru/security/login
class LogInPage(WildberriesPage):
    path = "security/login"

    def __init__(self, driver: Chrome, authorization_driver: Remote = None) -> None:
        super().__init__(driver)
        self.authorization_driver = authorization_driver

        self.geo_link = ExtendedWebElement(self, '//span[contains(@class, "geocity-link")]')
        self.main_banner_container = ExtendedWebElement(
            self,
            '//div[contains(@class, "swiper-container j-main-banners")]'
        )
        self.phone_number_input = ExtendedWebElement(self, '//input[@class = "input-item"]')
        self.get_code_button = ExtendedWebElement(self, '//button[@id = "requestCode"]')
        # noinspection SpellCheckingInspection
        self.code_inputs = ExtendedWebElementCollection(self, '//input[@class = "input-item j-b-charinput"]')

    def log_in_manually(self) -> None:
        options = ChromeOptions()
        # этот параметр тоже нужен, так как в режиме headless с некоторыми элементами нельзя взаимодействовать
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        self.driver = Chrome(options = options, service = service)
        self.driver.maximize_window()

        self.open()
        input("\nНажмите ввод (enter), когда завершите авторизацию\n")

    def log_in(self) -> None:
        with open(settings.LOG_IN_CREDENTIALS_PATH, 'r') as file:
            credentials = json.load(file)
        self.phone_number_input.send_keys(credentials["phone"][1:])
        self.get_code_button.click()

        events_page = EventsPage(self.authorization_driver)
        events_page.open()

        for code_input, char in zip(self.code_inputs, events_page.get_log_in_code()):
            code_input: ExtendedWebElement
            code_input.send_keys(char)
