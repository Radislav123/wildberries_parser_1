from typing import Any

import telebot
from telebot import types

import logger
from core import models as core_models
from parser_price import models as parser_price_models
from . import models as bot_telegram_models, settings


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
        CHANGES_PRICE = '🟪'
        CHANGES_PERSONAL_SALE = '🟦'
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
            return cls.wall(f"[{cls.wall(data)}]({link})")

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

        @classmethod
        def join(cls, text: list[str]) -> str:
            return "\n".join([cls.escape(string) for string in text])

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
            notification.new.item.link
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
                    f"{self.Token.CHANGES_PRICE} {block_name} изменилась",
                    f"{emoji} {block_name}: {notification.new.price} <==="
                    f" {self.Formatter.strikethrough(notification.old.price)}"
                    f" {self.Formatter.changes_repr(notification.new.price, notification.old.price)} ₽"
                ]
            else:
                block = [
                    f"{self.Token.CHANGES_PRICE} {block_name} изменилась",
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
                    f"{self.Token.CHANGES_PERSONAL_SALE} {block_name} изменилась",
                    f"{emoji} {block_name}: {notification.new.personal_sale} <==="
                    f" {self.Formatter.strikethrough(notification.old.personal_sale)}"
                    f" {self.Formatter.changes_repr(notification.new.personal_sale, notification.old.personal_sale)} %"
                ]
            else:
                block = [
                    f"{self.Token.CHANGES_PERSONAL_SALE} {block_name} изменилась",
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

            text = self.Formatter.join(text)
            self.send_message(
                notification.new.item.user.telegram_chat_id,
                text,
                self.ParseMode.MARKDOWN,
                disable_web_page_preview = True
            )

            # дублируется сообщение для другого пользователя по просьбе заказчика
            # user_id заказчика
            if notification.new.item.user.telegram_user_id == 245207096:
                self.send_message(
                    5250931949,
                    text,
                    self.ParseMode.MARKDOWN,
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
        self.set_commands_list()

    def register_handlers(self) -> None:
        # команды для пользователей
        self.message_handler(commands = ["start"])(self.start)
        self.message_handler(commands = ["save_chat_id"])(self.save_chat_id)

        self.message_handler(commands = ["add_item"])(self.add_item)
        self.message_handler(commands = ["remove_item"])(self.remove_item)
        self.message_handler(commands = ["get_all_items"])(self.get_all_items)

        # команды для заказчика
        self.message_handler(commands = ["send_to_users"])(self.send_to_users)
        self.callback_query_handler(
            lambda callback: callback.data.startswith("send_to_users")
        )(self.send_to_users_callback_send)
        self.callback_query_handler(
            lambda callback: callback.data.startswith("cancel_send_to_users")
        )(self.send_to_users_callback_cancel)

        # проверка отписки от каналов
        self.chat_member_handler()(self.notify_unsubscriber)

    def set_commands_list(self) -> None:
        customer_commands = [
            types.BotCommand("send_to_users", "Рассылка пользователям")
        ]
        user_commands = [
            types.BotCommand("start", "Регистрация"),
            # types.BotCommand("save_chat_id", "Специальная команда"),
            types.BotCommand("add_item", "Добавить товар в отслеживаемые"),
            types.BotCommand("remove_item", "Убрать товар из отслеживаемых"),
            types.BotCommand("get_all_items", "Список всех отслеживаемых товаров")
        ]

        customer_scope = types.BotCommandScopeChat(chat_id = core_models.ParserUser.get_customer().telegram_chat_id)
        user_scope = types.BotCommandScopeAllPrivateChats()

        self.set_my_commands(customer_commands, customer_scope)
        self.set_my_commands(user_commands, user_scope)

    def start_polling(self) -> None:
        self.logger.info("Telegram bot is running")
        # todo: перейти на polling, чтобы обрабатывать все исключения самостоятельно
        self.infinity_polling(allowed_updates = telebot.util.update_types, restart_on_change = True)

    @staticmethod
    def get_parser_user(telegram_user: types.User) -> core_models.ParserUser | None:
        try:
            user = core_models.ParserUser.objects.get(telegram_user_id = telegram_user.id)
        except core_models.ParserUser.DoesNotExist:
            user = None
        return user

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

    # чтобы бот корректно мог проверять подписки, он должен быть администратором канала
    # https://core.telegram.org/bots/api#getchatmember
    def check_user_subscriptions(self, user: core_models.ParserUser) -> list[int]:
        not_subscribed = []
        for chat_id in self.settings.NEEDED_SUBSCRIPTIONS:
            subscribed = False
            try:
                telegram_user = self.get_chat_member(chat_id, user.telegram_user_id)
                if telegram_user.status in self.settings.CHANNEL_SUBSCRIPTION_STATUSES:
                    subscribed = True
            except telebot.apihelper.ApiTelegramException:
                pass

            if not subscribed:
                not_subscribed.append(chat_id)
        return not_subscribed

    def notify_unsubscriber(self, update: types.ChatMemberUpdated) -> None:
        if update.new_chat_member.status in self.settings.CHANNEL_NON_SUBSCRIPTION_STATUSES \
                and (user := self.get_parser_user(update.from_user)) is not None:
            not_subscribed = self.check_user_subscriptions(user)
            if len(not_subscribed) == 1:
                link = self.Formatter.link('канал', self.settings.NEEDED_SUBSCRIPTIONS[not_subscribed[0]])
                text = [f"Подпишитесь на {link}, чтобы пользоваться ботом."]
            else:
                text = [
                    f"Подпишитесь на каналы, чтобы пользоваться ботом:",
                    *[self.Formatter.link(f"канал {index}", self.settings.NEEDED_SUBSCRIPTIONS[x])
                      for index, x in enumerate(not_subscribed, 1)]
                ]
            self.send_message(
                user.telegram_chat_id,
                self.Formatter.join(text),
                self.ParseMode.MARKDOWN
            )

    def add_item(self, message: types.Message) -> None:
        # todo: запускать парсинги для обычных пользователей и для заказчика раздельно
        # todo: добавить ограничение на 10 одновременно отслеживаемых товаров
        # todo: добавить скрипт, удаляющий записи старше недели всех пользователей, кроме заказчика
        user = self.get_parser_user(message.from_user)

        item = parser_price_models.Item(user = user)
        self.register_next_step_handler(message, self.add_item_step_name, user, item)
        self.send_message(
            user.telegram_chat_id,
            "Введите свое название для товара."
        )

    def add_item_step_name(
            self,
            message: types.Message,
            user: core_models.ParserUser,
            item: parser_price_models.Item
    ) -> None:
        item.name = message.text
        self.register_next_step_handler(message, self.add_item_step_vendor_code, user, item)
        self.send_message(
            user.telegram_chat_id,
            "Введите артикул товара."
        )

    def add_item_step_vendor_code(
            self,
            message: types.Message,
            user: core_models.ParserUser,
            item: parser_price_models.Item
    ) -> None:
        item.vendor_code = int(message.text)
        item.save()
        text = [
            f"{self.Formatter.link(item.vendor_code, item.link)} добавлен для отслеживания."
        ]
        self.send_message(
            user.telegram_chat_id,
            self.Formatter.join(text),
            self.ParseMode.MARKDOWN
        )

    def remove_item(self, message: types.Message) -> None:
        user = self.get_parser_user(message.from_user)
        self.send_message(
            user.telegram_chat_id,
            "Введите артикул товара."
        )
        self.register_next_step_handler(message, self.remove_item_step_vendor_code, user)

    def remove_item_step_vendor_code(self, message: types.Message, user: core_models.ParserUser) -> None:
        vendor_code = int(message.text)
        item = parser_price_models.Item.objects.get(user = user, vendor_code = vendor_code)
        text = [
            f"{self.Formatter.link(item.vendor_code, item.link)} убран из отслеживаемых."
        ]
        prices = parser_price_models.Price.objects.filter(item__vendor_code = vendor_code, item__user = user)
        prices.delete()
        item.delete()
        self.send_message(
            user.telegram_chat_id,
            self.Formatter.join(text),
            self.ParseMode.MARKDOWN
        )

    def get_all_items(self, message: types.Message) -> None:
        user = self.get_parser_user(message.from_user)
        items = parser_price_models.Item.objects.filter(user = user)
        if len(items) == 0:
            text = ["У Вас еще нет отслеживаемых товаров."]
        else:
            text = [f"{self.Formatter.link(item.name, item.link)}: {item.vendor_code}" for item in items]

        text_chunks = telebot.util.smart_split(self.Formatter.join(text))
        for text_chunk in text_chunks:
            self.send_message(
                user.telegram_chat_id,
                text_chunk,
                self.ParseMode.MARKDOWN,
                disable_web_page_preview = True
            )

    def send_to_users(self, message: types.Message) -> None:
        user = self.get_parser_user(message.from_user)
        self.send_message(
            user.telegram_chat_id,
            "Введите сообщение, которое хотите отправить."
        )
        self.register_next_step_handler(message, self.send_to_users_step_message, user)

    def send_to_users_step_message(self, message: types.Message, user: core_models.ParserUser) -> None:
        message_to_send = bot_telegram_models.SendToUsers(user = user, telegram_message_id = message.id)
        message_to_send.save()

        self.copy_message(
            user.telegram_chat_id,
            user.telegram_chat_id,
            message_to_send.telegram_message_id
        )

        send_button = types.InlineKeyboardButton("Разослать", callback_data = f"send_to_users:{message_to_send.id}")
        cancel_button = types.InlineKeyboardButton(
            "Отменить рассылку",
            callback_data = f"cancel_send_to_users:{message_to_send.id}"
        )
        reply_markup = types.InlineKeyboardMarkup()
        reply_markup.add(send_button, cancel_button)
        self.send_message(
            user.telegram_chat_id,
            "Сообщение выше отображается также, как будет отображаться пользователям.",
            reply_markup = reply_markup
        )

    def send_to_users_callback_send(self, callback: types.CallbackQuery) -> None:
        message_to_send = bot_telegram_models.SendToUsers.objects.get(id = callback.data.split(':')[-1])

        for user in core_models.ParserUser.objects.exclude(username = message_to_send.user):
            self.copy_message(
                user.telegram_chat_id,
                message_to_send.user.telegram_chat_id,
                message_to_send.telegram_message_id
            )
        message_to_send.sent = True
        message_to_send.save()

        self.edit_message_reply_markup(
            message_to_send.user.telegram_chat_id,
            callback.message.message_id
        )
        self.send_message(message_to_send.user.telegram_chat_id, "Сообщение разослано пользователям.")

    def send_to_users_callback_cancel(self, callback: types.CallbackQuery) -> None:
        message_to_send = bot_telegram_models.SendToUsers.objects.get(id = callback.data.split(':')[-1])
        message_to_send.sent = False
        message_to_send.save()

        self.edit_message_reply_markup(
            message_to_send.user.telegram_chat_id,
            callback.message.message_id
        )
        self.send_message(message_to_send.user.telegram_chat_id, "Сообщение не будет разослано пользователям.")
