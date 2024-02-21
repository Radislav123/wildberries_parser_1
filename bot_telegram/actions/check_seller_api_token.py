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
    callback_id = CallbackData.CHECK_SELLER_API_TOKEN

    @classmethod
    @base.BaseAction.open_menu_after_action
    @seller_api_token_filter
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        bot.send_message(user.telegram_chat_id, "Ваш токен действителен.")
