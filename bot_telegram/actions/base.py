from typing import TYPE_CHECKING

from telebot import types

from bot_telegram import settings
from core import models as core_models


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class BaseAction:
    settings = settings.Settings()

    command: str
    description: str
    button_text: str
    callback_id: str

    @classmethod
    def get_button(cls) -> types.InlineKeyboardButton:
        return types.InlineKeyboardButton(cls.button_text, callback_data = cls.callback_id)

    @classmethod
    def execute(cls, bot: "Bot", user: core_models.ParserUser, callback: types.CallbackQuery) -> None:
        raise NotImplementedError()
