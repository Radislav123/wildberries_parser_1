from typing import TYPE_CHECKING

from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import subscription_filter
from core import models as core_models
from parser_price import models as parser_price_models


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class RemoveItemAction(base.BaseAction):
    command = "remove_item"
    description = "Убрать товар из отслеживаемых"
    callback_id = CallbackData.REMOVE_ITEM

    @classmethod
    @subscription_filter
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        bot.send_message(
            user.telegram_chat_id,
            "Введите артикул товара."
        )
        bot.register_next_step_handler(callback.message, cls.step_vendor_code, bot, user)

    @classmethod
    @base.BaseAction.open_menu_after_action
    def step_vendor_code(cls, message: types.Message, bot: "Bot", user: core_models.ParserUser) -> None:
        vendor_code = int(message.text)
        items = parser_price_models.Item.objects.filter(user = user, vendor_code = vendor_code)
        text = [f"{bot.Formatter.link(item.vendor_code, item.link)} убран из отслеживаемых."
                for item in items]
        prices = parser_price_models.Price.objects.filter(item__vendor_code = vendor_code, item__user = user)
        prices.delete()
        items.delete()
        bot.send_message(
            user.telegram_chat_id,
            bot.Formatter.join(text),
            bot.ParseMode.MARKDOWN
        )
