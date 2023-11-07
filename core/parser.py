import datetime
import logging
import os
import pathlib

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

import logger
from . import models, settings


class UnsuccessfulParsing(Exception):
    pass


class Parser:
    settings = settings.Settings()
    logger: logging.LoggerAdapter
    parsing: models.Parsing
    parsing_type: str = None

    def setup_method(self):
        self.parsing = models.Parsing(type = self.parsing_type, duration = datetime.timedelta())
        self.parsing.save()
        os.environ["PARSING_ID"] = str(self.parsing.id)
        self.parsing.not_parsed_items = {}
        self.logger = logger.Logger(self.settings.APP_NAME)
        self.logger.info("Start")

    def teardown_method(self):
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
