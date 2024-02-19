from typing import TYPE_CHECKING

from telebot import types


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class BaseAction:
    button_text: str
    callback_id: str

    @classmethod
    def get_button(cls) -> types.InlineKeyboardButton:
        return types.InlineKeyboardButton(cls.button_text, callback_data = cls.callback_id)

    @classmethod
    def execute(cls, message: types.CallbackQuery, bot: "Bot") -> None:
        raise NotImplementedError()
