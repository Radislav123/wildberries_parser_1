from parsing_helper.web_elements import ExtendedWebElement

from .wildberries_base_page import WildberriesPage


# page_url = https://www.wildberries.ru/lk/details
class LKDetailsPage(WildberriesPage):
    path = "lk/details"

    def __init__(self, parser) -> None:
        super().__init__(parser)
        self.personal_sale = ExtendedWebElement(self, '//b[@class = "discount__numb discount__numb--color"]')
