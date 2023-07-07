from core import settings

from .apps import ParserPriceConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = ParserPriceConfig.name

    def __init__(self):
        super().__init__()

        # порядок отображение динамических полей в административной панели
        self.DYNAMIC_FIELDS_ORDER = ["final_price", "price", "personal_sale"]
