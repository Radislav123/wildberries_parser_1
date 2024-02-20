from typing import TYPE_CHECKING

from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import subscription_filter
from core import models as core_models
from parser_seller_api.parser import Parser as ParserSellerApi, RequestException


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class UpdateSellerApiTokenAction(base.BaseAction):
    command = "update_seller_api_token"
    description = "Обновить токен продавца"
    button_text = command
    callback_id = CallbackData.UPDATE_SELLER_API_TOKEN

    @classmethod
    @subscription_filter
    def execute(cls, bot: "Bot", user: core_models.ParserUser, callback: types.CallbackQuery) -> None:
        bot.register_next_step_handler(callback.message, cls.step_update_token, bot, user)
        bot.send_message(
            user.telegram_chat_id,
            bot.Formatter.join(
                [
                    "Введите токен продавца.",
                    "",
                    "Достаточно прав только на чтение.",
                    f"{bot.Formatter.link('Инструкция', 'https://openapi.wildberries.ru/general/authorization/ru/')}"
                    f" по генерации токена."
                ]
            ),
            bot.ParseMode.MARKDOWN
        )

    @classmethod
    def step_update_token(cls, message: types.Message, bot: "Bot", user: core_models.ParserUser) -> None:
        new_token = message.text
        user.seller_api_token = new_token

        try:
            ParserSellerApi.make_request(user)
        except RequestException:
            bot.send_message(
                user.telegram_chat_id,
                "Токен не обновлен, потому что не валиден."
            )
        else:
            user.save()
            bot.send_message(
                user.telegram_chat_id,
                "Вы успешно обновили токен продавца."
            )
        finally:
            bot.delete_message(user.telegram_chat_id, message.message_id)
