from selenium.webdriver import Remote

from web_elements import ExtendedWebElement
from .wildberries_base_page import WildberriesPage


# page_url = https://www.wildberries.ru/lk/newsfeed/events
class EventsPage(WildberriesPage):
    path = "lk/newsfeed/events"

    def __init__(self, driver: Remote) -> None:
        super().__init__(driver)

        self.code_text = ExtendedWebElement(self, '//span[contains(text(), "Код подтверждения")]')

    def get_log_in_code(self) -> str:
        return self.code_text.text.split()[2][:-1]
