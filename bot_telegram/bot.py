from typing import Any

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
            token = self.settings.secrets.bot_telegram.token

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

    @staticmethod
    def cross_out(data: Any) -> str:
        return "".join(['\u0336'.join(str(data)), '\u0336', ' '])

    def notify_prices_changed(
            self,
            # [(new_price, old_price, price_changing, personal_sale_changing)]
            changed_prices: list[tuple[parser_price_models.Price, parser_price_models.Price, float, int]]
    ) -> None:
        for new_price, old_price, price_changing, personal_sale_changing in changed_prices:
            text = []

            if price_changing != 0:
                text.append(f"🟪 Изменилась цена")
            if personal_sale_changing != 0:
                text.append(f"🟦 Изменилась СПП")
            text.append("")

            text.extend(
                [
                    f"{new_price.item.get_field_verbose_name('category')}: {new_price.item.category}",
                    f"{new_price.item.get_field_verbose_name('vendor_code')}: {new_price.item.vendor_code}",
                    f"{new_price.item.get_field_verbose_name('name')}: {new_price.item.name}",
                    ""
                ]
            )

            price_emoji = '💰'
            price_name = new_price.get_field_verbose_name('final_price')
            new_price_string = new_price.final_price
            old_price_string = self.cross_out(old_price.final_price)
            if price_changing > 0:
                text.extend(
                    [
                        "🟥",
                        # todo: добавить хранение и парсинг валюты
                        f"{price_emoji} {price_name}: {new_price_string} <=== {old_price_string} +{price_changing} ₽",
                    ]
                )
            elif price_changing < 0:
                text.extend(
                    [
                        "🟩",
                        f"{price_emoji} {price_name}: {new_price_string} <=== {old_price_string} {price_changing} ₽",
                    ]
                )
            else:
                text.append(f"{price_emoji} {price_name}: {new_price_string} ₽", )
            text.append("")

            personal_sale_emoji = '🧮'
            personal_sale_name = new_price.get_field_verbose_name('personal_sale')
            new_personal_sale_string = new_price.personal_sale
            old_personal_sale_string = self.cross_out(old_price.personal_sale)
            if personal_sale_changing > 0:
                text.extend(
                    [
                        "🟥",
                        f"{personal_sale_emoji} {personal_sale_name}: {new_personal_sale_string}"
                        f" <=== {old_personal_sale_string} +{personal_sale_changing} %",
                    ]
                )
            elif personal_sale_changing < 0:
                text.extend(
                    [
                        "🟩",
                        f"{personal_sale_emoji} {personal_sale_name}: {new_personal_sale_string}"
                        f" <=== {old_personal_sale_string} {personal_sale_changing} %",
                    ]
                )
            else:
                text.append(f"{personal_sale_emoji} {personal_sale_name}: {new_personal_sale_string} %")

            self.send_message(new_price.item.user.telegram_chat_id, "\n".join(text))
