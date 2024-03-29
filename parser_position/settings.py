from core import settings

from .apps import ParserPositionConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = ParserPositionConfig.name

    def __init__(self):
        super().__init__()

        # количество дней для расчета долгих изменений позиции
        self.LONG_MOVEMENT_DELTA = 5

        # порядок отображение динамических полей в административной панели
        self.DYNAMIC_FIELDS_ORDER = ["position_repr", "movement"]

        self.PROMO_SEPARATOR = "<="
