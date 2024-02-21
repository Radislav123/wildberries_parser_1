from typing import TYPE_CHECKING

from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import seller_api_token_filter, subscription_filter
from core import models as core_models


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class CheckSubscriptionsAction(base.BaseAction):
    command = "check_subscriptions"
    description = "Проверить необходимые подписки"
    callback_id = CallbackData.CHECK_SUBSCRIPTIONS

    @classmethod
    @base.BaseAction.open_menu_after_action
    @subscription_filter
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        bot.send_message(user.telegram_chat_id, "Вы подписаны на все необходимые каналы.")
        seller_api_token_filter(lambda *args: None)(cls, bot, user, callback)
