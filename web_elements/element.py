from typing import Callable, TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import element_to_be_clickable, presence_of_element_located, \
    visibility_of_element_located
from selenium.webdriver.support.wait import WebDriverWait

from parser_project import project_settings


if TYPE_CHECKING:
    from pages.base_page import BasePage


class ExtendedWebElement:
    class WaitCondition:
        CLICKABLE = element_to_be_clickable
        PRESENCE = presence_of_element_located
        VISIBLE = visibility_of_element_located

    def __init__(self, page: "BasePage", xpath: str) -> None:
        self.page = page
        self.driver = page.driver

        self.xpath = xpath
        self.wait = WebDriverWait(self.driver, project_settings.DEFAULT_TIMEOUT)
        self.initialized: dict[Callable, bool] = {}
        self._selenium_element: None | WebElement = None

    def reset(self) -> None:
        """Сбрасывает состояние объекта к первоначальному."""

        self.initialized = {}
        self._selenium_element = None

    def init_if_necessary(self, wait_condition: Callable = WaitCondition.PRESENCE) -> None:
        if wait_condition not in self.initialized or not self.initialized[wait_condition]:
            self.init(wait_condition)

    def init(self, wait_condition: Callable = WaitCondition.PRESENCE) -> None:
        """Находит элемент в DOM-структуре страницы."""

        self._selenium_element = self.wait.until(wait_condition((By.XPATH, self.xpath)))
        self.initialized[wait_condition] = True

    @property
    def selenium_element(self) -> WebElement:
        self.init_if_necessary()
        return self._selenium_element

    @property
    def text(self) -> str:
        self.init_if_necessary()
        return self.selenium_element.text

    def click(self) -> None:
        self.init(self.WaitCondition.CLICKABLE)
        return self.selenium_element.click()

    def send_keys(self, value: str) -> None:
        self.init_if_necessary()
        return self.selenium_element.send_keys(value)

    def get_attribute(self, name) -> str:
        self.init_if_necessary()
        return self.selenium_element.get_attribute(name)
