from core import settings

from .apps import BotTelegramConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = BotTelegramConfig.name

    def __init__(self):
        super().__init__()

        # список с id чатов/каналов на которые пользователь должен быть подписан, чтобы использовать бота
        self.NEEDED_SUBSCRIPTIONS = [-1001922384556, -1001638911900]
        self.CHANNEL_SUBSCRIPTION_STATUSES = ["creator", "administrator", "member"]
