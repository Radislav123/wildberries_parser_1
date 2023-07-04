import logging

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from logger import Logger
from . import models, settings


class ParserCore:
    settings = settings.Settings()
    logger: logging.Logger
    driver: Chrome
    parsing: models.Parsing

    @classmethod
    def setup_class(cls):
        cls.logger = Logger("parser")

    def setup_method(self):
        self.parsing = models.Parsing()
        self.parsing.save()
        self.logger.info("Start")

        options = ChromeOptions()
        # этот параметр тоже нужен, так как в режиме headless с некоторыми элементами нельзя взаимодействовать
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        self.driver = Chrome(options = options, service = service)
        self.driver.maximize_window()

    def teardown_method(self):
        self.driver.quit()
