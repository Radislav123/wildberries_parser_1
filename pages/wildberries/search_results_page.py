from parsing_helper.web_elements import ExtendedWebElementCollection

from .wildberries_base_page import WildberriesPage


# page_url =
# https://www.wildberries.ru/catalog/0/search.aspx?search=%D1%84%D0%BE%D1%80%D0%BC%D0%B0%20%D0%B1%D1%83%D0%BA%D0%B2%D1%8B
class SearchResultsPage(WildberriesPage):
    def __init__(self, parser, page_number: int, keyword: str) -> None:
        super().__init__(parser)
        self.keyword = keyword
        self.path = f"catalog/0/search.aspx?page={page_number}&search={self.keyword}"
        self.items = ExtendedWebElementCollection(self, "//article[@data-nm-id]")
