from typing import TYPE_CHECKING

from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import seller_api_token_filter
from core import models as core_models
from core.service import validators


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class UpdateSubscriptionsAction(base.BaseAction):
    command = "update_subscriptions"
    description = "Обновить информацию по подпискам в боте"
    button_text = command
    callback_id = CallbackData.UPDATE_SUBSCRIPTIONS

    @classmethod
    def execute(cls, bot: "Bot", user: core_models.ParserUser, callback: types.CallbackQuery) -> None:
        not_subscribed = bot.get_needed_subscriptions(user)
        user.update_subscriptions_info(not_subscribed)

        if not validators.validate_subscriptions(user):
            reply_markup = types.InlineKeyboardMarkup([bot.get_subscription_buttons(not_subscribed)])
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join([bot.SUBSCRIPTION_TEXT]),
                bot.ParseMode.MARKDOWN,
                reply_markup = reply_markup
            )
        else:
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join(["Вы подписаны на все необходимые каналы. Информация в боте обновлена."]),
                bot.ParseMode.MARKDOWN
            )
            seller_api_token_filter(lambda *args: None)(cls, bot, user, callback)
