from core import settings

from .apps import ParserPriceConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = ParserPriceConfig.name

    def __init__(self):
        super().__init__()

        # порядок отображения динамических полей в административной панели
        self.DYNAMIC_FIELDS_ORDER = ["final_price", "price", "personal_discount"]

        # количество парсингов пользователей, хранимых для пользователей
        self.USER_HISTORY_DEPTH = 10
