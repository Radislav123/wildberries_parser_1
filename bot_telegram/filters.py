from typing import Any, Callable, TYPE_CHECKING

from telebot import types

from bot_telegram.actions.base import BaseAction
from core import models as core_models
from core.service import validators


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


def customer_filter(function: Callable) -> Callable:
    def wrapper(
            cls: type[BaseAction],
            callback: types.CallbackQuery,
            bot: "Bot",
            user: core_models.ParserUser,
            *args,
            **kwargs
    ) -> Any:
        if user != core_models.ParserUser.get_customer() and user != core_models.ParserUser.get_developer():
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join(["Только заказчик может пользоваться данной командой."]),
                bot.ParseMode.MARKDOWN
            )
        else:
            return function(cls, callback, bot, user, *args, **kwargs)

    return wrapper


def developer_filter(function: Callable) -> Callable:
    def wrapper(
            cls: type[BaseAction],
            callback: types.CallbackQuery,
            bot: "Bot",
            user: core_models.ParserUser,
            *args,
            **kwargs
    ) -> Any:
        if user != core_models.ParserUser.get_developer():
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join(["Только разработчик может пользоваться данной командой."]),
                bot.ParseMode.MARKDOWN
            )
        else:
            return function(cls, callback, bot, user, *args, **kwargs)

    return wrapper


def subscription_filter(function: Callable) -> Callable:
    def wrapper(
            cls: type[BaseAction],
            callback: types.CallbackQuery,
            bot: "Bot",
            user: core_models.ParserUser,
            *args,
            **kwargs
    ) -> Any:
        if not validators.validate_subscriptions(user):
            not_subscribed = bot.get_needed_subscriptions(user)
            reply_markup = types.InlineKeyboardMarkup([bot.get_subscription_buttons(not_subscribed)])
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join([bot.SUBSCRIPTION_TEXT]),
                bot.ParseMode.MARKDOWN,
                reply_markup = reply_markup
            )
        else:
            return function(cls, callback, bot, user, *args, **kwargs)

    return wrapper


def seller_api_token_filter(function: Callable) -> Callable:
    def wrapper(
            cls: type[BaseAction],
            callback: types.CallbackQuery,
            bot: "Bot",
            user: core_models.ParserUser,
            *args,
            **kwargs
    ) -> Any:
        if not validators.validate_seller_api_token(user):
            reply_markup = types.InlineKeyboardMarkup(((bot.get_update_seller_api_token_button(),),))

            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join([bot.SELLER_API_TEXT]),
                bot.ParseMode.MARKDOWN,
                reply_markup = reply_markup
            )
        else:
            return function(cls, callback, bot, user, *args, **kwargs)

    return wrapper
