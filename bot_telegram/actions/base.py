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
    def action_wrapper(open_menu_after_call: bool) -> Callable:
        def error_handler(function: Callable) -> Callable:
            def wrapper(
                    cls: "type[BaseAction]",
                    callback_or_message: types.Message | types.CallbackQuery,
                    bot: "Bot",
                    user: core_models.ParserUser,
                    *args,
                    **kwargs
            ) -> Any:
                if isinstance(callback_or_message, types.Message):
                    message = callback_or_message
                else:
                    message = callback_or_message.message
                try:
                    result = function(cls, callback_or_message, bot, user, *args, **kwargs)
                    if open_menu_after_call:
                        bot.menu(message, False)
                except Exception as error:
                    bot.send_message(user.telegram_chat_id, "Произошла ошибка. Попробуйте еще раз чуть позже.")
                    bot.menu(message, False)
                    raise error
                return result

            return wrapper

        return error_handler

    @classmethod
    def get_button(cls) -> types.InlineKeyboardButton:
        return types.InlineKeyboardButton(cls.button_text, callback_data = cls.callback_id)

    @classmethod
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        raise NotImplementedError()
