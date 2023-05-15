from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait

from parser_project import parser_settings


if TYPE_CHECKING:
    from pages import BasePage


class ExtendedWebElement:
    def __init__(self, page: "BasePage", xpath: str):
        self.page = page
        self.driver = page.driver
        self.xpath = xpath
        self.wait = WebDriverWait(self.driver, parser_settings.DEFAULT_TIMEOUT)
        self.initialized = False
        self.selenium_element: None | WebElement = None

    def init(self):
        """Находит элемент в DOM-структуре страницы."""

        self.selenium_element = self.wait.until(presence_of_element_located((By.XPATH, self.xpath)))
        self.initialized = True

    @property
    def text(self) -> str:
        if not self.initialized:
            self.init()
        return self.selenium_element.text
