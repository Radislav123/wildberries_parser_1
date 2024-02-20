from typing import TYPE_CHECKING

from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import subscription_filter
from core import models as core_models
from parser_price import models as parser_price_models


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class AddItemAction(base.BaseAction):
    command = "add_item"
    description = "Добавить товар в отслеживаемые"
    button_text = command
    callback_id = CallbackData.ADD_ITEM

    @classmethod
    @subscription_filter
    def execute(cls, bot: "Bot", user: core_models.ParserUser, callback: types.CallbackQuery) -> None:
        current_items = parser_price_models.Item.objects.filter(user = user)
        if len(current_items) > cls.settings.MAX_USER_ITEMS:
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join(
                    [
                        f"У Вас уже отслеживается товаров: {len(current_items)}.",
                        "Удалите лишние товары, чтобы добавить новый."
                    ]
                ),
                bot.ParseMode.MARKDOWN
            )
        else:
            new_item = parser_price_models.Item(user = user, name_site = "Название появится после ближайшего парсинга")
            bot.register_next_step_handler(callback.message, cls.step_vendor_code, bot, user, new_item)
            bot.send_message(
                user.telegram_chat_id,
                "Введите артикул товара."
            )

    @classmethod
    def step_vendor_code(
            cls,
            message: types.Message,
            bot: "Bot",
            user: core_models.ParserUser,
            item: parser_price_models.Item
    ) -> None:
        item.vendor_code = int(message.text)
        item.save()
        text = [
            f"{bot.Formatter.link(item.vendor_code, item.link)} добавлен для отслеживания."
        ]
        bot.send_message(
            user.telegram_chat_id,
            bot.Formatter.join(text),
            bot.ParseMode.MARKDOWN
        )
