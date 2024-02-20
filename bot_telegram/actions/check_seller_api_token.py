from typing import TYPE_CHECKING

from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import seller_api_token_filter
from core import models as core_models


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class CheckSellerApiTokenAction(base.BaseAction):
    command = "check_seller_api_token"
    description = "Проверить действительность токена API продавца"
    button_text = command
    callback_id = CallbackData.CHECK_SELLER_API_TOKEN

    @classmethod
    @seller_api_token_filter
    def execute(cls, bot: "Bot", user: core_models.ParserUser, callback: types.CallbackQuery) -> None:
        bot.send_message(
            user.telegram_chat_id,
            bot.Formatter.join(["Ваш токен действителен."]),
            bot.ParseMode.MARKDOWN
        )
