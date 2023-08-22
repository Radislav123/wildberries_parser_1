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

    @classmethod
    def setup_class(cls):
        cls.logger = logger.Logger(cls.settings.APP_NAME)

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

        cache_manager = DriverCacheManager(root_dir = pathlib.Path.cwd())
        driver_manager = ChromeDriverManager(cache_manager = cache_manager).install()
        service = Service(executable_path = driver_manager)

        self.driver = Chrome(options = options, service = service)
        self.driver.maximize_window()
        self.driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})

    def teardown_method(self):
        self.driver.quit()
