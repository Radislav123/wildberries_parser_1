from core import settings

from .apps import ParserPositionConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = ParserPositionConfig.name

    def __init__(self):
        super().__init__()

        # количество попыток запросить товары на странице
        self.REQUEST_PAGE_ITEMS_ATTEMPTS_AMOUNT = 10

        # количество дней для расчета долгих изменений позиции
        self.LONG_MOVEMENT_DELTA = 5
