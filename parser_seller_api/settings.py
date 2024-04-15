from core import settings

from parser_seller_api.apps import ParserSellerApiConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = ParserSellerApiConfig.name
    parallel = False

    def __init__(self) -> None:
        super().__init__()

        self.PRICE_RANGES = (
            (0, 300),
            (300, 500),
            (500, 1000),
            (1000, 3000),
            (3000, 5000),
            (5000, 10000),
            (10000, 2147483647)
        )
