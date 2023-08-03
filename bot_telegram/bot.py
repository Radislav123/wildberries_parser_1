from typing import Any

import telebot
from telebot import types

import logger
from core import models as core_models
from parser_price import models as parser_price_models
from . import settings


class BotTelegramException(Exception):
    pass


class NotEnoughEscapeWallsException(BotTelegramException):
    pass


class WrongNotificationTypeException(BotTelegramException):
    pass


class BotService:
    class ParseMode:
        MARKDOWN = "MarkdownV2"

    class Token:
        UP = '⬆'
        DOWN = '⬇'
        NO_CHANGES = '⏺'
        CHANGES = '🟪'
        NO_PERSONAL_SALE = '🟥'
        OWNERSHIP = "❗❗❗"

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger.Logger(self.settings.APP_NAME)


class NotifierMixin(BotService):
    @staticmethod
    def check_ownership(price: parser_price_models.Price) -> bool:
        own_labels = ["мои", "мое", "моё", "мой"]
        name = price.item.name.lower()
        ownership = False
        for label in own_labels:
            if label in name:
                ownership = True
                break
        return ownership

    def construct_start_block(self, notification: parser_price_models.Price.Notification) -> list[str]:
        if self.check_ownership(notification.new):
            block = [self.Token.OWNERSHIP]
        else:
            block = []

        if notification.new.item.category is not None:
            block.append(
                f"{notification.new.item.category.get_field_verbose_name('name')}:"
                f" {notification.new.item.category.name}"
            )

        link_string = self.Formatter.link(
            notification.new.item.name_site,
            f'https://www.wildberries.ru/catalog/{notification.new.item.vendor_code}/detail.aspx'
        )
        block.extend(
            [
                f"{notification.new.item.get_field_verbose_name('name_site')}: {link_string}",
                f"{notification.new.item.get_field_verbose_name('vendor_code')}: {notification.new.item.vendor_code}",
                f"{notification.new.item.get_field_verbose_name('name')}: {notification.new.item.name}"
            ]
        )

        return block

    def construct_final_block(self) -> list[str]:
        block = [fr"* {self.Formatter.italic('Указана максимальная скидка для клиента')}"]
        return block

    # todo: добавить хранение и парсинг валюты
    def construct_price_block(self, notification: parser_price_models.Price.Notification) -> list[str]:
        block_name = notification.new.get_field_verbose_name("price")

        if notification.new.price != notification.old.price:
            if notification.new.price is not None and notification.old.price is not None:
                if notification.new.price > notification.old.price:
                    emoji = self.Token.UP
                else:
                    emoji = self.Token.DOWN

                block = [
                    f"{self.Token.CHANGES} {block_name} изменилась",
                    f"{emoji} {block_name}: {notification.new.price} <==="
                    f" {self.Formatter.strikethrough(notification.old.price)}"
                    f" {self.Formatter.changes_repr(notification.new.price, notification.old.price)} ₽"
                ]
            else:
                block = [
                    f"{self.Token.CHANGES} {block_name} изменилась",
                    f"{self.Token.NO_CHANGES} {block_name}: {notification.new.price} <==="
                    f" {self.Formatter.strikethrough(notification.old.price)} ₽"
                ]
        else:
            block = [f"{self.Token.NO_CHANGES} {block_name}: {notification.new.price}"]

        return block

    def construct_personal_sale_block(self, notification: parser_price_models.Price.Notification) -> list[str]:
        block_name = notification.new.get_field_verbose_name("personal_sale")

        if notification.new.personal_sale != notification.old.personal_sale:
            if notification.new.personal_sale is not None and notification.old.personal_sale is not None:
                if notification.new.personal_sale > notification.old.personal_sale:
                    emoji = self.Token.UP
                else:
                    emoji = self.Token.DOWN

                block = [
                    f"{self.Token.CHANGES} {block_name} изменилась",
                    f"{emoji} {block_name}: {notification.new.personal_sale} <==="
                    f" {self.Formatter.strikethrough(notification.old.personal_sale)}"
                    f" {self.Formatter.changes_repr(notification.new.personal_sale, notification.old.personal_sale)} %"
                ]
            else:
                block = [
                    f"{self.Token.CHANGES} {block_name} изменилась",
                    f"{self.Token.NO_CHANGES} {block_name}: {notification.new.personal_sale} <==="
                    f" {self.Formatter.strikethrough(notification.old.personal_sale)} %"
                ]
        else:
            block = [f"{self.Token.NO_CHANGES} {block_name}: {notification.new.personal_sale}"]

        return block

    def construct_final_price_block(self, notification: parser_price_models.Price.Notification) -> list[str]:
        block_name = notification.new.get_field_verbose_name("final_price")

        if notification.new.final_price != notification.old.final_price:
            if notification.new.final_price is not None and notification.old.final_price is not None:
                if notification.new.final_price > notification.old.final_price:
                    emoji = self.Token.UP
                else:
                    emoji = self.Token.DOWN

                block = [
                    f"{emoji} {block_name}: {notification.new.final_price} <==="
                    f" {self.Formatter.strikethrough(notification.old.final_price)}"
                    f" {self.Formatter.changes_repr(notification.new.final_price, notification.old.final_price)} ₽"
                ]
            else:
                block = [
                    f"{self.Token.NO_CHANGES} {block_name}: {notification.new.final_price} <==="
                    f" {self.Formatter.strikethrough(notification.old.final_price)} ₽"
                ]
        else:
            block = [f"{self.Token.NO_CHANGES} {block_name}: {notification.new.final_price}"]
        return block

    @staticmethod
    def construct_sold_out_block() -> list[str]:
        return ["Товар распродан"]

    def construct_no_personal_sale_block(self) -> list[str]:
        return [f"{self.Token.NO_PERSONAL_SALE} Скидка постоянного покупателя отсутствует"]

    def notify(self, notifications: list[parser_price_models.Price.Notification]) -> None:
        for notification in notifications:
            if not notification.sold_out and not notification.no_personal_sale:
                text = [
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
            elif notification.sold_out:
                text = [
                    *self.construct_start_block(notification),
                    "",
                    *self.construct_sold_out_block()
                ]
            elif notification.no_personal_sale:
                text = [
                    *self.construct_start_block(notification),
                    "",
                    *self.construct_price_block(notification),
                    "",
                    *self.construct_no_personal_sale_block(),
                    "",
                    *self.construct_final_price_block(notification),
                    "",
                    *self.construct_final_block()
                ]
            else:
                raise WrongNotificationTypeException()

            text = "\n".join([self.Formatter.escape(string) for string in text])
            self.send_message(
                notification.new.item.user.telegram_chat_id,
                text,
                parse_mode = self.ParseMode.MARKDOWN,
                disable_web_page_preview = True
            )

            # дублируется сообщение для другого пользователя по просьбе заказчика
            # chat_id заказчика
            if notification.new.item.user.telegram_chat_id == 898581629:
                self.send_message(
                    5250931949,
                    text,
                    parse_mode = self.ParseMode.MARKDOWN,
                    disable_web_page_preview = True
                )

    send_message = telebot.TeleBot.send_message


# todo: перейти с поллинга на вебхук
class Bot(NotifierMixin, telebot.TeleBot):
    def __init__(self, token: str = None):
        if token is None:
            token = self.settings.secrets.bot_telegram.token

        super().__init__(token)
        self.register_handlers()

    def register_handlers(self):
        self.message_handler(commands = ["start"])(self.start)
        self.message_handler(commands = ["save_chat_id"])(self.save_chat_id)

    def start(self, message: types.Message) -> None:
        try:
            user = core_models.ParserUser.objects.get(
                telegram_user_id = message.from_user.id,
                telegram_chat_id = message.chat.id
            )
            text = "Вы уже были зарегистрированы. Повторная регистрация невозможна"
        except core_models.ParserUser.DoesNotExist:
            user = core_models.ParserUser(
                telegram_user_id = message.from_user.id,
                telegram_chat_id = message.chat.id
            )
            user.save()
            text = "Вы зарегистрированы."

        self.send_message(user.telegram_chat_id, text)

    def save_chat_id(self, message: types.Message) -> None:
        with open("temp_chat_id.txt", 'w') as file:
            file.write(f"{message.chat.id}\n")

        text = "Идентификатор чата сохранен."
        self.send_message(message.chat.id, text)
