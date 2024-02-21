from typing import TYPE_CHECKING

from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import subscription_filter
from core import models as core_models
from parser_seller_api.parser import Parser as ParserSellerApi, RequestException


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class UpdateSellerApiTokenAction(base.BaseAction):
    command = "update_seller_api_token"
    description = "Обновить токен продавца"
    callback_id = CallbackData.UPDATE_SELLER_API_TOKEN

    image_path = f"{base.BaseAction.settings.ACTIONS_DATA_PATH}/update_seller_api_token_0.jpg"
    with open(image_path, "rb") as file:
        image = file.read()

    @classmethod
    @subscription_filter
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        text = [
            "Для отображения СПП необходимо ввести токен.",
            f"{bot.Formatter.link('Инструкция', 'https://openapi.wildberries.ru/general/authorization/ru/')}"
            f" по генерации токена на сайте Wildberries.",
            "",
            "1) Это безопасно?",
            "Да, для этого необходимо поставить галочку в поле \"Только на чтение\".",
            "Тогда с помощью этого токена нельзя будет менять никакие данные.",
            "",
            "2) Для работы необходимо выбрать категорию \"Цены и скидки\".",
            "",
            "3) Сгенерируйте токен, нажав \"Создать токен\".",
            "",
            "Ниже введите полученный токен продавца."
        ]

        if cls.image_path in bot.cache:
            image_id = bot.cache[cls.image_path]
            image_message = bot.send_photo(user.telegram_chat_id, image_id, text)
        else:
            image_message = bot.send_photo(user.telegram_chat_id, cls.image, text)
            # изображение с максимальным разрешением
            bot.cache[cls.image_path] = image_message.photo[-1].file_id

        bot.register_next_step_handler(callback.message, cls.step_update_token, bot, user, image_message)

    @classmethod
    @base.BaseAction.open_menu_after_action
    def step_update_token(
            cls,
            message: types.Message,
            bot: "Bot",
            user: core_models.ParserUser,
            image_message: types.Message
    ) -> None:
        new_token = message.text
        user.seller_api_token = new_token

        try:
            ParserSellerApi.make_request(user)
        except RequestException:
            bot.send_message(user.telegram_chat_id, "Токен не обновлен, потому что не валиден.")
        else:
            user.save()
            bot.send_message(user.telegram_chat_id, "Вы успешно обновили токен продавца.")
        finally:
            bot.delete_message(user.telegram_chat_id, image_message.message_id)
            bot.delete_message(user.telegram_chat_id, message.message_id)
