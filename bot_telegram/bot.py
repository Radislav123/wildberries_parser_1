import telebot

from telebot import types
import logger
from core import models as core_models
from parser_price import models as parser_price_models
from . import settings


class Bot(telebot.TeleBot):
    settings = settings.Settings()

    def __init__(self, token: str = None):
        if token is None:
            token = self.settings.secrets.telegram_bot.token

        super().__init__(token)
        self.logger = logger.Logger(self.settings.APP_NAME)

        self.message_handler(commands = ["start"])(self.start)

    def start(self, message: types.Message) -> None:
        # todo: добавить логику создания аккаунта
        admin = core_models.ParserUser.get_admin()
        admin.telegram_id = message.from_user.id
        admin.telegram_chat_id = message.chat.id
        admin.save()

        text = "Вы подписаны на изменения цен.\nЗакройте окно командной строки, открытое для авторизации."
        self.send_message(message.from_user.id, text)

    def notify_price_changed(self, changed_prices: dict[parser_price_models.Price, parser_price_models.Price]) -> None:
        self.logger.debug(changed_prices)
        for new_price in changed_prices:
            old_price = changed_prices[new_price]
            text = [
                f"{new_price.item.get_field_verbose_name('vendor_code')}: {new_price.item.vendor_code}",
                f"{new_price.item.get_field_verbose_name('name')}: {new_price.item.name}",
                f"{new_price.get_field_verbose_name('final_price')} новая: {new_price.final_price}",
                f"{old_price.get_field_verbose_name('final_price')} прошлая: {old_price.final_price}",
                f"{new_price.get_field_verbose_name('personal_sale')} новая: {new_price.personal_sale}",
                f"{old_price.get_field_verbose_name('personal_sale')} прошлая: {old_price.personal_sale}",
            ]
            self.send_message(new_price.item.user.telegram_chat_id, "\n".join(text))
