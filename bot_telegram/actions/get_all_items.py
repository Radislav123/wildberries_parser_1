from typing import TYPE_CHECKING

import telebot
from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import subscription_filter
from core import models as core_models
from parser_price import models as parser_price_models


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class GetAllItemsAction(base.BaseAction):
    command = "get_all_items"
    description = "Получить список всех отслеживаемых товаров"
    callback_id = CallbackData.GET_ALL_ITEMS

    @classmethod
    @base.BaseAction.open_menu_after_action
    @subscription_filter
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        items = parser_price_models.Item.objects.filter(user = user)
        if len(items) == 0:
            text = ["У Вас еще нет отслеживаемых товаров."]
        else:
            text = [f"{bot.Formatter.link(item.name_site, item.link)}: {item.vendor_code}" for item in items]

        text_chunks = telebot.util.smart_split(bot.Formatter.join(text))
        for text_chunk in text_chunks:
            bot.send_message(
                user.telegram_chat_id,
                text_chunk,
                bot.ParseMode.MARKDOWN,
                link_preview_options = types.LinkPreviewOptions(True)
            )
