from core import settings

from .apps import BotTelegramConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = BotTelegramConfig.name

    def __init__(self):
        super().__init__()

        # каналы на которые пользователь должен быть подписан, чтобы использовать бота
        # todo: перенести в БД?
        self.NEEDED_SUBSCRIPTIONS = {
            -1001922384556: ("https://t.me/mpwbfair", "канал 1"),
            -1001638911900: ("https://t.me/ivan_shkitin", "канал 2")
        }
        self.CHANNEL_SUBSCRIPTION_STATUSES = ["creator", "administrator", "member"]
        self.CHANNEL_NON_SUBSCRIPTION_STATUSES = ["left"]

        # количество последних разосланных сообщений пользователям, хранимых в БД
        self.SEND_TO_USER_KEEP_AMOUNT = 50
        # максимальное количество отслеживаемых товаров для пользователя
        self.MAX_USER_ITEMS = 10
