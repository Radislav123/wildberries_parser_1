import datetime
import logging

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

import logger
from . import models, settings
import pathlib


class UnsuccessfulParsing(Exception):
    pass


class Parser:
    settings = settings.Settings()
    logger: logging.Logger
    driver: Chrome
    parsing: models.Parsing
    parsing_type: str = None
    headless = True

    @classmethod
    def setup_class(cls):
        cls.logger = logger.Logger(cls.settings.APP_NAME)

    def setup_method(self):
        self.parsing = models.Parsing(type = self.parsing_type, duration = datetime.timedelta())
        self.parsing.save()
        self.parsing.not_parsed_items = {}
        self.logger.info("Start")

        driver_options = ChromeOptions()
        # этот параметр тоже нужен, так как в режиме headless с некоторыми элементами нельзя взаимодействовать
        driver_options.add_argument("--no-sandbox")
        driver_options.add_argument("--disable-blink-features=AutomationControlled")
        if self.headless:
            driver_options.add_argument("--headless")
        driver_options.add_argument("--window-size=1920,1080")
        driver_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        cache_manager = DriverCacheManager(root_dir = pathlib.Path.cwd())
        driver_manager = ChromeDriverManager(cache_manager = cache_manager).install()
        driver_service = Service(executable_path = driver_manager)

        self.driver = Chrome(options = driver_options, service = driver_service)
        self.driver.maximize_window()
        self.driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})

    def teardown_method(self):
        self.driver.quit()
        if len(self.parsing.not_parsed_items) > 0:
            self.logger.info(f"Not parsed items: {self.parsing.not_parsed_items}")
            self.parsing.success = False
            self.parsing.save()

            exception = UnsuccessfulParsing(*list(self.parsing.not_parsed_items.values()))
            raise exception from exception.args[-1]
        else:
            self.parsing.not_parsed_items = None
            self.parsing.success = True
            self.parsing.save()
