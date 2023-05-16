from typing import Callable, TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import element_to_be_clickable, presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait

from parser_project import project_settings


if TYPE_CHECKING:
    from pages.base_page import BasePage


class ExtendedWebElement:
    def __init__(self, page: "BasePage", xpath: str) -> None:
        self.page = page
        self.driver = page.driver

        self.xpath = xpath
        self.wait = WebDriverWait(self.driver, project_settings.DEFAULT_TIMEOUT)
        self.initialized = False
        self.selenium_element: None | WebElement = None

    def init(self, wait_condition: Callable = presence_of_element_located) -> None:
        """Находит элемент в DOM-структуре страницы."""

        self.selenium_element = self.wait.until(wait_condition((By.XPATH, self.xpath)))
        self.initialized = True

    @property
    def text(self) -> str:
        if not self.initialized:
            self.init()
        return self.selenium_element.text

    def click(self) -> None:
        self.init(element_to_be_clickable)
        return self.selenium_element.click()

    def send_keys(self, value: str) -> None:
        if not self.initialized:
            self.init()
        return self.selenium_element.send_keys(value)
