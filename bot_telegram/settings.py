import platform

from core import settings
from .apps import BotTelegramConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = BotTelegramConfig.name

    def __init__(self):
        super().__init__()

        self.RESOURCES_PATH = f"{self.RESOURCES_PATH}/{self.APP_NAME}"
        self.ACTIONS_DATA_PATH = f"{self.RESOURCES_PATH}/actions"

        # каналы на которые пользователь должен быть подписан, чтобы использовать бота
        # todo: перенести в БД или секреты?
        self.NEEDED_SUBSCRIPTIONS = {
            -1001922384556: ("https://t.me/mpwbfair", "канал 1"),
            -1001638911900: ("https://t.me/+gukqwJCmpm1jMGUy", "канал 2")
        }
        self.CHANNEL_SUBSCRIPTION_STATUSES = ["creator", "administrator", "member"]
        self.CHANNEL_NON_SUBSCRIPTION_STATUSES = ["left"]

        # количество последних разосланных сообщений пользователям, хранимых в БД
        self.SEND_TO_USER_KEEP_AMOUNT = 50
        # максимальное количество отслеживаемых товаров для пользователя
        self.MAX_USER_ITEMS = 10

        # максимальное количество сообщений от бота в секунду
        self.API_MESSAGES_PER_SECOND_LIMIT = 10 if platform.node() != self.secrets.developer.pc_name else 30
