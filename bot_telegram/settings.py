from core import settings

from .apps import BotTelegramConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = BotTelegramConfig.name

    def __init__(self):
        super().__init__()
