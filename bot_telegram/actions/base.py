from typing import Any, Callable, TYPE_CHECKING

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

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls.button_text = cls.description

    @staticmethod
    def open_menu_after_action(function) -> Callable:
        def wrapper(
                cls: "type[BaseAction]",
                callback_or_message: types.Message | types.CallbackQuery,
                bot: "Bot",
                *args,
                **kwargs
        ) -> Any:
            try:
                result = function(cls, callback_or_message, bot, *args, **kwargs)
            except Exception as error:
                raise error
            finally:
                if isinstance(callback_or_message, types.Message):
                    message = callback_or_message
                else:
                    message = callback_or_message.message
                bot.menu(message, False)
            return result

        return wrapper

    @classmethod
    def get_button(cls) -> types.InlineKeyboardButton:
        return types.InlineKeyboardButton(cls.button_text, callback_data = cls.callback_id)

    @classmethod
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        raise NotImplementedError()
