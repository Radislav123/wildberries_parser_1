from typing import Any

import telebot
from telebot import types

import logger
from core import models as core_models
from parser_price import models as parser_price_models
from . import settings


class NotEnoughEscapeWallsException(Exception):
    pass


class Bot(telebot.TeleBot):
    class ParseMode:
        MARKDOWN = "MarkdownV2"

    class Emoji:
        UP = '⬆'
        DOWN = '⬇'
        NO_CHANGES = '⏺'
        CHANGES = '🟦'

    class Formatter:
        ESCAPE_WALL = "|||"

        @classmethod
        def wall(cls, data: Any) -> str:
            return f"{cls.ESCAPE_WALL}{data}{cls.ESCAPE_WALL}"

        @classmethod
        def strikethrough(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mstrikethrough(str(data)))

        @classmethod
        def italic(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mitalic(str(data)))

        @classmethod
        def link(cls, data: Any, link: str) -> str:
            return cls.wall(f"[{data}]({link})")

        @classmethod
        def escape(cls, string: str) -> str:
            # текст между "|||" не будет экранирован (cls.ESCAPE_WALL)
            # "escaped text ||| not escaped text ||| more escaped text ||| more not escaped text ||| more escaped text"
            chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

            chunks = string.split(cls.ESCAPE_WALL)
            if len(chunks) % 2 == 0:
                raise NotEnoughEscapeWallsException()
            for number in range(len(chunks)):
                if number % 2 == 0:
                    for char in chars_to_escape:
                        chunks[number] = chunks[number].replace(char, '\\' + char)
            return "".join(chunks)

        @staticmethod
        def changes_repr(new: int | float, old: int | float) -> str:
            changing = new - old
            if changing > 0:
                sign = '+'
            else:
                sign = ''
            return f"{sign}{changing}"

    settings = settings.Settings()

    def __init__(self, token: str = None):
        if token is None:
            token = self.settings.secrets.bot_telegram.token

        super().__init__(token)
        self.logger = logger.Logger(self.settings.APP_NAME)

        self.message_handler(commands = ["start"])(self.start)

    def start(self, message: types.Message) -> None:
        # todo: добавить логику создания аккаунта
        admin = core_models.ParserUser.get_admin()
        admin.telegram_id = message.from_user.id
        admin.telegram_chat_id = message.chat.id
        admin.save()

        text = "Вы подписаны на изменения цен."
        self.send_message(message.from_user.id, text)

    def construct_start_block(self, notification: parser_price_models.Price.Notification) -> list[str]:
        item = notification.new.item

        if item.category is not None:
            block = [f"{item.category.get_field_verbose_name('name')}: {item.category.name}"]
        else:
            block = []

        link_string = self.Formatter.link(
            item.vendor_code,
            f'https://www.wildberries.ru/catalog/{item.vendor_code}/detail.aspx'
        )
        block.extend(
            [
                f"{item.get_field_verbose_name('name_site')}: {item.name_site}",
                f"{item.get_field_verbose_name('vendor_code')}: {link_string}",
                f"{item.get_field_verbose_name('name')}: {item.name}"
            ]
        )

        return block

    # todo: добавить хранение и парсинг валюты
    def construct_price_block(self, notification: parser_price_models.Price.Notification) -> list[str]:
        new_price = notification.new
        old_price = notification.old

        block_name = new_price.get_field_verbose_name("price")

        if new_price.price != old_price.price:
            if new_price.price is not None and old_price.price is not None:
                if new_price.price > old_price.price:
                    emoji = self.Emoji.UP
                else:
                    emoji = self.Emoji.DOWN

                block = [
                    f"{self.Emoji.CHANGES} {block_name} изменилась",
                    f"{emoji} {block_name}: {new_price.price} <=== {self.Formatter.strikethrough(old_price.price)}"
                    f" {self.Formatter.changes_repr(new_price.price, old_price.price)} ₽"
                ]
            else:
                block = [
                    f"{self.Emoji.CHANGES} {block_name} изменилась",
                    f"{self.Emoji.NO_CHANGES} {block_name}: {new_price.price} <==="
                    f" {self.Formatter.strikethrough(old_price.price)} ₽"
                ]
        else:
            block = [f"{self.Emoji.NO_CHANGES} {block_name}: {new_price.price}"]

        return block

    def construct_personal_sale_block(self, notification: parser_price_models.Price.Notification) -> list[str]:
        new_price = notification.new
        old_price = notification.old

        block_name = new_price.get_field_verbose_name("personal_sale")

        if new_price.personal_sale != old_price.personal_sale:
            if new_price.personal_sale is not None and old_price.personal_sale is not None:
                if new_price.personal_sale > old_price.personal_sale:
                    emoji = self.Emoji.UP
                else:
                    emoji = self.Emoji.DOWN

                block = [
                    f"{self.Emoji.CHANGES} {block_name} изменилась",
                    f"{emoji} {block_name}: {new_price.personal_sale} <==="
                    f" {self.Formatter.strikethrough(old_price.personal_sale)}"
                    f" {self.Formatter.changes_repr(new_price.personal_sale, old_price.personal_sale)} %"
                ]
            else:
                block = [
                    f"{self.Emoji.CHANGES} {block_name} изменилась",
                    f"{self.Emoji.NO_CHANGES} {block_name}: {new_price.personal_sale} <==="
                    f" {self.Formatter.strikethrough(old_price.personal_sale)} %"
                ]
        else:
            block = [f"{self.Emoji.NO_CHANGES} {block_name}: {new_price.personal_sale}"]

        return block

    def construct_final_price_block(self, notification: parser_price_models.Price.Notification) -> list[str]:
        new_price = notification.new
        old_price = notification.old

        block_name = new_price.get_field_verbose_name("final_price")

        if new_price.final_price != old_price.final_price:
            if new_price.final_price is not None and old_price.final_price is not None:
                if new_price.final_price > old_price.final_price:
                    emoji = self.Emoji.UP
                else:
                    emoji = self.Emoji.DOWN

                block = [
                    f"{emoji} {block_name}: {new_price.final_price} <==="
                    f" {self.Formatter.strikethrough(old_price.final_price)}"
                    f" {self.Formatter.changes_repr(new_price.final_price, old_price.final_price)} ₽"
                ]
            else:
                block = [
                    f"{self.Emoji.NO_CHANGES} {block_name}: {new_price.final_price} <==="
                    f" {self.Formatter.strikethrough(old_price.final_price)} ₽"
                ]
        else:
            block = [f"{self.Emoji.NO_CHANGES} {block_name}: {new_price.final_price}"]
        return block

    def construct_final_block(self) -> list[str]:
        block = [fr"* {self.Formatter.italic('Указана максимальная скидка для клиента')}"]
        return block

    def notify_prices_changed(self, notifications: list[parser_price_models.Price.Notification]) -> None:
        for notification in notifications:
            text: list[str] = [
                *self.construct_start_block(notification),
                "",
                *self.construct_price_block(notification),
                "",
                *self.construct_personal_sale_block(notification),
                "",
                *self.construct_final_price_block(notification),
                "",
                *self.construct_final_block()
            ]

            self.send_message(
                notification.new.item.user.telegram_chat_id,
                "\n".join([self.Formatter.escape(string) for string in text]),
                parse_mode = self.ParseMode.MARKDOWN,
                disable_web_page_preview = True
            )
