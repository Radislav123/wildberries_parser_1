import platform
import time
from typing import Any, Callable, Iterable

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
from telebot.handler_backends import State, StatesGroup
from telebot.storage.base_storage import StateStorageBase

import logger
from bot_telegram.actions import *
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import customer_filter, developer_filter
from core import models as core_models
from core.service import validators
from parser_price import models as parser_price_models
from . import models, settings


Subscriptions = dict[int, tuple[str, str]]


class UserState(State):
    pass


class UserStatesGroup(StatesGroup):
    MENU = UserState()


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
        CHANGES_PERSONAL_DISCOUNT = '🟦'
        NO_PERSONAL_discount = '🟥'
        OWNERSHIP = "❗❗❗"

    class Formatter:
        ESCAPE_WALL = "|!&!|"

        @classmethod
        def wall(cls, data: Any) -> str:
            return f"{cls.ESCAPE_WALL}{data}{cls.ESCAPE_WALL}"

        @classmethod
        def remove_walls(cls, data: Any) -> str:
            if isinstance(data, str) and data.startswith(cls.ESCAPE_WALL) and data.endswith(cls.ESCAPE_WALL):
                string = "".join(data.split(cls.ESCAPE_WALL))
            else:
                string = str(data)
            return string

        @classmethod
        def copyable(cls, data: Any) -> str:
            return cls.wall(f"`{str(data)}`")

        @classmethod
        def underline(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.munderline(str(data)))

        @classmethod
        def bold(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mbold(str(data)))

        @classmethod
        def code(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mcode(str(data)))

        @classmethod
        def spoiler(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mspoiler(str(data)))

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
            # текст между cls.ESCAPE_WALL не будет экранирован
            # "escaped text |wall| not escaped text |wall| more escaped text
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
        def join(cls, text: Iterable[str]) -> str:
            return "\n".join([cls.escape(string) for string in text])

    class Wildberries:
        def __init__(self, bot: "BotService") -> None:
            self.bot = bot
            self.dest = self.bot.settings.MOSCOW_CITY_DICT["dest"]

    settings = settings.Settings()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger = logger.Logger(self.settings.APP_NAME)
        self.wildberries = self.Wildberries(self)


class NotifierMixin(BotService):
    SUBSCRIPTION_TEXT = (f"❗️Чтобы пользоваться ботом, подпишитесь на каналы."
                         f" Если вы подписаны на все каналы, функционал станет доступен автоматически."
                         f" Если этого не произошло используйте опцию меню "
                         f"«{CheckSubscriptionsAction.button_text}».")
    SELLER_API_TEXT = (f"Чтобы пользоваться расширенным функционалом,"
                       f" введите токен продавца, используя опцию меню {UpdateSellerApiTokenAction.button_text}.")

    # noinspection PyPep8Naming
    @property
    def BOT_GENERATION_TEXT(self) -> str:
        return f"Данное сообщение сгенерировано ботом (@{self.user.username})."

    @staticmethod
    def check_ownership(price: parser_price_models.Price) -> bool:
        ownership = False
        if price.item.user == core_models.ParserUser.get_customer():
            own_labels = ["мои", "мое", "моё", "мой"]
            name = price.item.name.lower()
            for label in own_labels:
                if label in name:
                    ownership = True
                    break
        return ownership

    def construct_header(
            self,
            category_name: str | None,
            vendor_code: int,
            name_site: str | None,
            name: str | None,
            link: str
    ) -> list[str]:
        block = []
        if category_name is not None:
            block.append(
                f"{parser_price_models.Category.get_field_verbose_name('name')}:"
                f" {category_name}"
            )

        link_string = self.Formatter.link(name_site, link)
        block.extend(
            [
                f"{parser_price_models.Item.get_field_verbose_name('name_site')}: {link_string}",
                f"{parser_price_models.Item.get_field_verbose_name('vendor_code')}: {vendor_code}"
            ]
        )
        if name is not None:
            block.append(f"{parser_price_models.Item.get_field_verbose_name('name')}: {name}")
        return block

    @property
    def link(self) -> str:
        return f"https://t.me/{self.user.username}"

    def construct_start_block(self, notification: parser_price_models.Notification) -> list[str]:
        block = []

        if self.check_ownership(notification.new):
            block.append(self.Token.OWNERSHIP)

        if notification.new.item.category is not None:
            category_name = notification.new.item.category.name
        else:
            category_name = None

        block.extend(
            self.construct_header(
                category_name,
                notification.new.item.vendor_code,
                notification.new.item.name_site,
                notification.new.item.name,
                notification.new.item.link
            )
        )

        return block

    def construct_final_block(self) -> list[str]:
        return [f"* {self.Formatter.italic('Указана максимальная скидка для клиента')}"]

    # todo: добавить хранение и парсинг валюты
    def construct_price_block(self, notification: parser_price_models.Notification) -> list[str]:
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

    def construct_personal_discount_block(self, notification: parser_price_models.Notification) -> list[str]:
        block_name = notification.new.get_field_verbose_name("personal_discount")
        new_personal_discount = notification.new.personal_discount
        old_personal_discount = notification.old.personal_discount
        if new_personal_discount is None:
            new_personal_discount = 0
        if old_personal_discount is None:
            old_personal_discount = 0

        if new_personal_discount != old_personal_discount:
            if new_personal_discount is not None and old_personal_discount is not None:
                if new_personal_discount > old_personal_discount:
                    emoji = self.Token.UP
                else:
                    emoji = self.Token.DOWN

                block = [
                    f"{self.Token.CHANGES_PERSONAL_DISCOUNT} {block_name} изменилась",
                    f"{emoji} {block_name}: {new_personal_discount} <==="
                    f" {self.Formatter.strikethrough(old_personal_discount)}"
                    f" {self.Formatter.changes_repr(new_personal_discount, old_personal_discount)} %"
                ]
            else:
                block = [
                    f"{self.Token.CHANGES_PERSONAL_DISCOUNT} {block_name} изменилась",
                    f"{self.Token.NO_CHANGES} {block_name}: {new_personal_discount} <==="
                    f" {self.Formatter.strikethrough(old_personal_discount)} %"
                ]
        else:
            block = [f"{self.Token.NO_CHANGES} {block_name}: {new_personal_discount}"]

        return block

    def construct_final_price_block(self, notification: parser_price_models.Notification) -> list[str]:
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

    @staticmethod
    def construct_appear_block() -> list[str]:
        return ["❗️ Товар появился в продаже"]

    def construct_no_personal_discount_block(self) -> list[str]:
        return [f"{self.Token.NO_PERSONAL_discount} СПП в процессе получения..."]

    @staticmethod
    def construct_no_seller_api_token_block() -> list[str]:
        return [
            "Токен продавца отсутствует.",
            "Чтобы видеть СПП, необходимо обновить токен продавца."
        ]

    def construct_bot_generation_block(self) -> list[str]:
        return [f"* {self.Formatter.italic(self.BOT_GENERATION_TEXT)}"]

    def notify(self, notifications: list[parser_price_models.Notification]) -> None:
        limit = self.settings.API_MESSAGES_PER_SECOND_LIMIT // self.settings.PYTEST_XDIST_WORKER_COUNT

        for notification_batch in [notifications[x:x + limit] for x in range(0, len(notifications), limit)]:
            for notification in notification_batch:
                try:
                    reply_markup = types.InlineKeyboardMarkup()
                    text = [*self.construct_start_block(notification), ]
                    # обычное оповещение
                    if not notification.new.sold_out and notification.new.personal_discount is not None:
                        if validators.validate_seller_api_token(notification.new.item.user):
                            if notification.new.price is not None:
                                text.extend(["", *self.construct_price_block(notification), ])
                            text.extend(["", *self.construct_personal_discount_block(notification), ])
                        else:
                            text.extend(["", *self.construct_no_seller_api_token_block(), ])
                            reply_markup.add(UpdateSellerApiTokenAction.get_button())
                        text.extend(
                            [
                                "", *self.construct_final_price_block(notification),
                                "", *self.construct_final_block(),
                            ]
                        )
                    # товар распродан
                    elif notification.new.sold_out and not notification.old.sold_out:
                        text.extend(["", *self.construct_sold_out_block()])
                    # товар появился в продаже
                    elif notification.old.sold_out and not notification.new.sold_out:
                        text.extend(
                            [
                                "", *self.construct_final_price_block(notification),
                                "", *self.construct_appear_block(),
                            ]
                        )
                    # СПП отсутствует
                    elif notification.new.personal_discount is None:
                        if validators.validate_seller_api_token(notification.new.item.user):
                            if notification.new.price is not None:
                                text.extend(["", *self.construct_price_block(notification), ])
                            text.extend(["", *self.construct_no_personal_discount_block(), ])
                        else:
                            text.extend(["", *self.construct_no_seller_api_token_block(), ])
                            reply_markup.add(UpdateSellerApiTokenAction.get_button())
                        text.extend(
                            [
                                "", *self.construct_final_price_block(notification),
                                "", *self.construct_final_block(),
                            ]
                        )
                    else:
                        raise WrongNotificationTypeException()
                    text.extend(self.construct_bot_generation_block())

                    # отправка оповещения разработчику, если бот запущен на машине разработчика
                    if platform.node() == self.settings.secrets.developer.pc_name:
                        telegram_chat_id = core_models.ParserUser.get_developer().telegram_chat_id
                        if notification.new.item.user == core_models.ParserUser.get_customer():
                            duplicated_telegram_chat_id = core_models.ParserUser.get_developer().telegram_chat_id
                        else:
                            duplicated_telegram_chat_id = None
                    else:
                        telegram_chat_id = notification.new.item.user.telegram_chat_id
                        if notification.new.item.user == core_models.ParserUser.get_customer():
                            # todo: перенести в секреты
                            duplicated_telegram_chat_id = 6528892715
                        else:
                            duplicated_telegram_chat_id = None

                    message = self.send_message(
                        telegram_chat_id,
                        text,
                        reply_markup = reply_markup,
                        link_preview_options = types.LinkPreviewOptions(True)
                    )

                    # дублируется сообщение для другого пользователя по просьбе заказчика
                    if duplicated_telegram_chat_id is not None:
                        try:
                            self.copy_message(duplicated_telegram_chat_id, message.chat.id, message.id)
                        except ApiTelegramException as error:
                            self.logger.info(str(error))

                    notification.delivered = True
                except Exception as error:
                    notification.delivered = False
                    notification.error = str(error)
                    raise error
                finally:
                    # todo: переделать на bulk_update
                    notification.save()
            time.sleep(1)

    send_message: Callable
    copy_message: Callable
    user: types.User


class UserStateMixin:
    current_states: StateStorageBase

    def set_state(self, user: core_models.ParserUser, state: UserState) -> bool:
        return self.current_states.set_state(user.telegram_chat_id, user.telegram_user_id, state)

    def get_state(self, user: core_models.ParserUser) -> UserState:
        return self.current_states.get_state(user.telegram_chat_id, user.telegram_user_id)

    def reset_state(self, user: core_models.ParserUser) -> bool:
        return self.delete_state(user)

    def delete_state(self, user: core_models.ParserUser) -> bool:
        return self.current_states.delete_state(user.telegram_chat_id, user.telegram_user_id)


# todo: перейти с поллинга на вебхук
class Bot(NotifierMixin, UserStateMixin, telebot.TeleBot):
    # общие команды
    common_commands = [
        types.BotCommand("start", "Регистрация"),
        types.BotCommand("menu", "Открыть меню бота"),
        types.BotCommand("get_chat_id", "Получить chat.id"),
    ]
    # команды для пользователей
    user_commands = []
    # команды для заказчика
    customer_commands = [
        types.BotCommand("send_to_users", "Рассылка пользователям"),
    ]
    # команды для разработчика
    developer_commands = [
        types.BotCommand("register_as_developer", "Сохранить Вас как разработчика в БД"),
        types.BotCommand("remove_user", "Удалить Вас из БД бота"),
        types.BotCommand("reset_command_list", "Сбросить список команд"),
    ]
    developer_commands.extend(customer_commands)
    developer_commands.extend(user_commands)
    user_commands.extend(common_commands)
    customer_commands.extend(common_commands)
    developer_commands.extend(common_commands)

    # действия
    menu_actions = (
        (GetDiscountsTableAction,),
        (ParseItemAction,),
        (GetAllItemsAction,),
        (AddItemAction,),
        (RemoveItemAction,),
        (CheckSubscriptionsAction,),
        (CheckSellerApiTokenAction,),
        (UpdateSellerApiTokenAction,),
    )
    callback_to_action: dict[str, type[BaseAction]] = {x.callback_id: x for actions in menu_actions for x in actions}
    menu_keyboard = types.InlineKeyboardMarkup([[x.get_button() for x in actions] for actions in menu_actions])
    menu_keyboard.add(types.InlineKeyboardButton("🇨🇳Условия нашего КАРГО WBFAIR", "https://t.me/mpwbfair/231"))

    def __init__(self, token: str = None):
        if token is None:
            token = self.settings.secrets.bot_telegram.token

        super().__init__(token)
        self.enable_saving_states()

    def send_message(
            self,
            chat_id: int | str,
            text: Iterable[str] | str,
            parse_mode: str = None,
            reply_markup: telebot.REPLY_MARKUP_TYPES = None,
            link_preview_options: types.LinkPreviewOptions = None,
            **kwargs
    ) -> types.Message:
        if isinstance(text, str):
            text = [text]
        if parse_mode is None:
            parse_mode = self.ParseMode.MARKDOWN

        text_chunks = telebot.util.smart_split(self.Formatter.join(text))
        for text_chunk in text_chunks:
            return super().send_message(
                chat_id,
                text_chunk,
                parse_mode,
                reply_markup = reply_markup,
                link_preview_options = link_preview_options,
                **kwargs
            )

    def send_photo(
            self,
            chat_id: int | str,
            photo_or_id: Any | str,
            text: Iterable[str] | str = None,
            parse_mode: str = None,
            reply_markup: telebot.REPLY_MARKUP_TYPES = None,
            **kwargs
    ) -> types.Message:
        if isinstance(text, str):
            text = [text]
        if parse_mode is None:
            parse_mode = self.ParseMode.MARKDOWN

        return super().send_photo(
            chat_id,
            photo_or_id,
            self.Formatter.join(text) if text is not None else text,
            parse_mode,
            reply_markup = reply_markup,
            **kwargs
        )

    def send_document(
            self,
            chat_id: int | str,
            document_or_id: Any | str,
            text: Iterable[str] | str = None,
            parse_mode: str = None,
            reply_markup: telebot.REPLY_MARKUP_TYPES = None,
            **kwargs
    ) -> types.Message:
        if isinstance(text, str):
            text = [text]
        if parse_mode is None:
            parse_mode = self.ParseMode.MARKDOWN

        return super().send_document(
            chat_id,
            document_or_id,
            caption = self.Formatter.join(text) if text is not None else text,
            parse_mode = parse_mode,
            reply_markup = reply_markup,
            **kwargs
        )

    copy_message = telebot.TeleBot.copy_message

    # добавлена, чтобы избежать цикличного импорта
    @staticmethod
    def get_update_seller_api_token_button() -> types.InlineKeyboardButton:
        return UpdateSellerApiTokenAction.get_button()

    def register_handlers(self) -> None:
        # общие команды
        for bot_command in self.common_commands:
            self.message_handler(commands = [bot_command.command])(getattr(self, bot_command.command))

        # команды для пользователей
        for bot_command in self.user_commands:
            self.message_handler(commands = [bot_command.command])(getattr(self, bot_command.command))

        # команды для заказчика
        for bot_command in self.customer_commands:
            self.message_handler(commands = [bot_command.command])(getattr(self, bot_command.command))
        self.callback_query_handler(
            lambda callback: callback.data.startswith(CallbackData.SEND_TO_USERS_SEND)
        )(self.send_to_users_callback_send)
        self.callback_query_handler(
            lambda callback: callback.data.startswith(CallbackData.SEND_TO_USERS_CANCEL)
        )(self.send_to_users_callback_cancel)

        # команды для разработчика
        for bot_command in self.developer_commands:
            self.message_handler(commands = [bot_command.command])(getattr(self, bot_command.command))

        # проверка изменения статуса пользователя в канале
        self.chat_member_handler()(self.check_user_status_change)

        # действия из меню
        self.callback_query_handler(
            lambda callback: callback.data.startswith(CallbackData.ACTION)
        )(self.action_resolver)

    def set_command_list_user(self) -> None:
        user_scope = types.BotCommandScopeAllPrivateChats()
        self.set_my_commands(self.user_commands, user_scope)

    def set_command_list_customer(self) -> None:
        try:
            customer_scope = types.BotCommandScopeChat(chat_id = core_models.ParserUser.get_customer().telegram_chat_id)
            self.set_my_commands(self.customer_commands, customer_scope)
        except AttributeError:
            pass

    def set_command_list_developer(self) -> None:
        try:
            developer_scope = types.BotCommandScopeChat(
                chat_id = core_models.ParserUser.get_developer().telegram_chat_id
            )
            self.set_my_commands(self.developer_commands, developer_scope)
        except (AttributeError, ApiTelegramException, core_models.ParserUser.DoesNotExist):
            pass

    def start_polling(self) -> None:
        self.register_handlers()
        self.set_command_list_user()
        self.set_command_list_customer()
        self.set_command_list_developer()

        self.logger.info("Telegram bot is running")
        self.infinity_polling(allowed_updates = telebot.util.update_types)

    @staticmethod
    def get_parser_user(telegram_user: types.User) -> core_models.ParserUser | None:
        try:
            user = core_models.ParserUser.objects.get(telegram_user_id = telegram_user.id)
        except core_models.ParserUser.DoesNotExist:
            user = None
        return user

    def check_pc(self, user: core_models.ParserUser) -> bool:
        on_developer_pc = (platform.node() == self.settings.secrets.developer.pc_name and
                           user == core_models.ParserUser.get_developer())
        not_on_developer_pc = (platform.node() != self.settings.secrets.developer.pc_name and
                               user != user == core_models.ParserUser.get_customer() and
                               user != user == core_models.ParserUser.get_developer())
        return on_developer_pc or not_on_developer_pc

    def check_user_status_change(self, update: types.ChatMemberUpdated) -> None:
        user = self.get_parser_user(update.from_user)
        if ((update.new_chat_member.status in self.settings.CHANNEL_NON_SUBSCRIPTION_STATUSES or
             update.new_chat_member.status in self.settings.CHANNEL_SUBSCRIPTION_STATUSES)
                and user is not None):
            CheckSubscriptionsAction.pure_execute(None, self, user)

    # todo: перенести в filters
    # чтобы бот мог корректно проверять подписки, он должен быть администратором канала
    # https://core.telegram.org/bots/api#getchatmember
    def get_needed_subscriptions(self, user: core_models.ParserUser) -> Subscriptions:
        not_subscribed = {}
        for chat_id, data in self.settings.NEEDED_SUBSCRIPTIONS.items():
            subscribed = False
            try:
                telegram_user = self.get_chat_member(chat_id, user.telegram_user_id)
                if telegram_user.status in self.settings.CHANNEL_SUBSCRIPTION_STATUSES:
                    subscribed = True
            except ApiTelegramException:
                pass

            if not subscribed:
                not_subscribed[chat_id] = data
        return not_subscribed

    @staticmethod
    def get_subscription_buttons(not_subscribed: Subscriptions) -> list[list[types.InlineKeyboardButton]]:
        keyboard = []
        for _, data in not_subscribed.items():
            keyboard.append([types.InlineKeyboardButton(data[1], url = data[0])])
        return keyboard

    def start(self, message: types.Message) -> None:
        try:
            user = core_models.ParserUser.objects.get(
                telegram_user_id = message.from_user.id,
                telegram_chat_id = message.chat.id
            )
            text = ["Вы уже были зарегистрированы. Повторная регистрация невозможна."]
            reply_markup = []
        except core_models.ParserUser.DoesNotExist:
            user = core_models.ParserUser(
                telegram_user_id = message.from_user.id,
                telegram_chat_id = message.chat.id,
                subscribed = False
            )
            user.save()
            text = [
                self.SUBSCRIPTION_TEXT,
                "",
                "После того, как подпишитесь, сможете отслеживать изменения цен.",
                "",
                f"На данный момент вы можете отслеживать товары в количестве {self.settings.MAX_USER_ITEMS}.",
                "",
                f"После ввода токена продавца ({UpdateSellerApiTokenAction.button_text})"
                f" сможете отслеживать изменения СПП."
            ]
            not_subscribed = self.get_needed_subscriptions(user)
            reply_markup = types.InlineKeyboardMarkup(self.get_subscription_buttons(not_subscribed))

        self.send_message(user.telegram_chat_id, text, reply_markup = reply_markup)

    def menu(self, message: types.Message, delete_message = True) -> None:
        if delete_message:
            self.delete_message(message.chat.id, message.id)
        text = "Меню бота"
        self.send_message(message.chat.id, text, reply_markup = self.menu_keyboard)

    def get_chat_id(self, message: types.Message) -> None:
        self.send_message(message.chat.id, self.Formatter.copyable(message.chat.id))

    @customer_filter
    def send_to_users(self, message: types.Message, user: core_models.ParserUser) -> None:
        self.send_message(user.telegram_chat_id, "Введите сообщение, которое хотите отправить.")
        self.register_next_step_handler(message, self.send_to_users_step_message, user)

    def send_to_users_step_message(self, message: types.Message, user: core_models.ParserUser) -> None:
        message_to_send = models.SendToUsers(user = user, telegram_message_id = message.id)
        message_to_send.save()

        self.copy_message(
            user.telegram_chat_id,
            user.telegram_chat_id,
            message_to_send.telegram_message_id
        )

        send_button = types.InlineKeyboardButton(
            "Разослать",
            callback_data = f"{CallbackData.SEND_TO_USERS_SEND}:{message_to_send.id}"
        )
        cancel_button = types.InlineKeyboardButton(
            "Отменить рассылку",
            callback_data = f"{CallbackData.SEND_TO_USERS_CANCEL}:{message_to_send.id}"
        )
        reply_markup = types.InlineKeyboardMarkup([[send_button, cancel_button]])
        self.send_message(
            user.telegram_chat_id,
            "Сообщение выше отображается также, как будет отображаться пользователям.",
            reply_markup = reply_markup
        )

    # todo: добавить сохранение ошибки при неуспешном отправлении
    def send_to_users_callback_send(self, callback: types.CallbackQuery) -> None:
        message_to_send = models.SendToUsers.objects.get(
            id = callback.data.split(CallbackData.DELIMITER)[-1]
        )

        if platform.node() == self.settings.secrets.developer.pc_name:
            users = [core_models.ParserUser.get_developer()]
        else:
            users = list(core_models.ParserUser.objects.exclude(username = message_to_send.user))

        for user_batch in [users[x:x + self.settings.API_MESSAGES_PER_SECOND_LIMIT]
                           for x in range(0, len(users), self.settings.API_MESSAGES_PER_SECOND_LIMIT)]:
            for user in user_batch:
                try:
                    self.copy_message(
                        user.telegram_chat_id,
                        message_to_send.user.telegram_chat_id,
                        message_to_send.telegram_message_id
                    )
                except ApiTelegramException as error:
                    if error.error_code == 403 and "bot was blocked by the user" in error.description:
                        self.logger.info("bot was blocked")
                    else:
                        self.logger.info(error.description)
            time.sleep(1)
        message_to_send.sent = True
        message_to_send.save()

        self.edit_message_reply_markup(
            message_to_send.user.telegram_chat_id,
            callback.message.message_id,
            reply_markup = types.InlineKeyboardMarkup()
        )
        self.send_message(message_to_send.user.telegram_chat_id, "Сообщение разослано пользователям.")

    def send_to_users_callback_cancel(self, callback: types.CallbackQuery) -> None:
        message_to_send = models.SendToUsers.objects.get(
            id = callback.data.split(CallbackData.DELIMITER)[-1]
        )
        message_to_send.sent = False
        message_to_send.save()

        self.edit_message_reply_markup(message_to_send.user.telegram_chat_id, callback.message.message_id)
        self.send_message(message_to_send.user.telegram_chat_id, "Сообщение не будет разослано пользователям.")

    # todo: переписать, чтобы регистрировал после добавления в БД
    def register_as_developer(self, message: types.Message) -> None:
        developer = core_models.ParserUser.get_developer()
        developer.telegram_user_id = message.from_user.id
        developer.telegram_chat_id = message.chat.id
        developer.save()
        self.set_command_list_developer()
        self.send_message(developer.telegram_chat_id, "Вы зарегистрированы как разработчик")

    @developer_filter
    def remove_user(self, message: types.Message, user: core_models.ParserUser) -> None:
        items = parser_price_models.Item.objects.filter(user = user)
        item_ids = list(items.values_list("id", flat = True))
        prices = parser_price_models.Price.objects.filter(item_id__in = item_ids)
        prices.delete()
        items.delete()
        user.delete()
        self.send_message(message.chat.id, "Вы были удалены из БД бота.")

    @developer_filter
    def reset_command_list(self, _: types.Message, user: core_models.ParserUser) -> None:
        scope = types.BotCommandScopeChat(user.telegram_chat_id)
        self.delete_my_commands(scope)
        self.send_message(user.telegram_chat_id, "Ваш список команд сброшен.")

    def action_resolver(self, callback: types.CallbackQuery) -> None:
        user = self.get_parser_user(callback.from_user)
        self.delete_message(user.telegram_chat_id, callback.message.message_id)
        self.callback_to_action[callback.data].execute(callback, self, user)
