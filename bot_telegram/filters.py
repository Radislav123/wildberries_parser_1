from typing import Any, Callable, TYPE_CHECKING

from telebot import types

from core import models as core_models
from core.service import validators


if TYPE_CHECKING:
    from bot_telegram.bot import Bot
    from bot_telegram.actions import BaseAction

# todo: remove this?
UPDATE_SUBSCRIPTIONS = "/update_subscriptions"
SUBSCRIPTION_TEXT = (f"Чтобы пользоваться ботом, подпишитесь на каналы,"
                     f" а потом используйте команду {UPDATE_SUBSCRIPTIONS} для обновления информации в боте.")
# todo: remove this?
UPDATE_SELLER_API_TOKEN = "/update_seller_api_token"
SELLER_API_TEXT = (f"Чтобы использовать эту команду,"
                   f" введите токен продавца, используя команду {UPDATE_SELLER_API_TOKEN}.")


def customer_filter(function: Callable) -> Callable:
    def wrapper(
            cls: "type[BaseAction]",
            bot: "Bot",
            user: core_models.ParserUser,
            callback: types.CallbackQuery,
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
            return function(cls, bot, user, callback, *args, **kwargs)

    return wrapper


def developer_filter(function: Callable) -> Callable:
    def wrapper(
            cls: "type[BaseAction]",
            bot: "Bot",
            user: core_models.ParserUser,
            callback: types.CallbackQuery,
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
            return function(cls, bot, user, callback, *args, **kwargs)

    return wrapper


def subscription_filter(function: Callable) -> Callable:
    def wrapper(
            cls: "type[BaseAction]",
            bot: "Bot",
            user: core_models.ParserUser,
            callback: types.CallbackQuery,
            *args,
            **kwargs
    ) -> Any:
        if not validators.validate_subscriptions(user):
            not_subscribed = bot.get_needed_subscriptions(user)
            reply_markup = types.InlineKeyboardMarkup([bot.construct_subscription_buttons(not_subscribed)])
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join([SUBSCRIPTION_TEXT]),
                bot.ParseMode.MARKDOWN,
                reply_markup = reply_markup
            )
        else:
            return function(cls, bot, user, callback, *args, **kwargs)

    return wrapper


def seller_api_token_filter(function: Callable) -> Callable:
    def wrapper(
            cls: "type[BaseAction]",
            bot: "Bot",
            user: core_models.ParserUser,
            callback: types.CallbackQuery,
            *args,
            **kwargs
    ) -> Any:
        if not validators.validate_seller_api_token(user):
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join([SELLER_API_TEXT]),
                bot.ParseMode.MARKDOWN
            )
        else:
            return function(cls, bot, user, callback, *args, **kwargs)

    return wrapper
