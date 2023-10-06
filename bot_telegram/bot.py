import pathlib
import platform
import time
from typing import Any, Callable

import telebot
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from telebot import types
from telebot.apihelper import ApiTelegramException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

import logger
from core import models as core_models
from core.service import parsing
from pages import MainPage
from parser_price import models as parser_price_models
from . import models as bot_telegram_models, settings


Subscriptions = dict[int, tuple[str, str]]

SUBSCRIPTION_TEXT = "Чтобы пользоваться ботом, подпишитесь на каналы."


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
        def join(cls, text: list[str]) -> str:
            return "\n".join([cls.escape(string) for string in text])

    class Wildberries:
        _dest: str = None
        _regions: str = None

        def __init__(self, bot: "BotService") -> None:
            self.bot = bot

        def prepare(self) -> None:
            self.bot.logger.info("Preparing wildberries attributes")

            driver_options = ChromeOptions()
            # этот параметр тоже нужен, так как в режиме headless с некоторыми элементами нельзя взаимодействовать
            driver_options.add_argument("--no-sandbox")
            driver_options.add_argument("--disable-blink-features=AutomationControlled")
            driver_options.add_argument("--headless")
            driver_options.add_argument("--window-size=1920,1080")
            driver_options.add_experimental_option("excludeSwitches", ["enable-logging"])

            cache_manager = DriverCacheManager(root_dir = pathlib.Path.cwd())
            driver_manager = ChromeDriverManager(cache_manager = cache_manager).install()
            driver_service = Service(executable_path = driver_manager)

            self.bot.driver = Chrome(options = driver_options, service = driver_service)
            self.bot.driver.maximize_window()
            self.bot.driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})

            # noinspection PyTypeChecker
            main_page = MainPage(self.bot)
            main_page.open()
            self._dest, self._regions = main_page.set_city(self.bot.settings.MOSCOW_CITY_DICT)

            self.bot.driver.quit()

        @property
        def dest(self) -> str:
            if self._dest is None:
                self.prepare()
            return self._dest

        @property
        def regions(self) -> str:
            if self._regions is None:
                self.prepare()
            return self._regions

    settings = settings.Settings()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger.Logger(self.settings.APP_NAME)
        self.wildberries = self.Wildberries(self)


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

    def construct_header(
            self,
            category_name: str | None,
            vendor_code: int,
            name_site: str,
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

    def construct_start_block(self, notification: parser_price_models.Notification) -> list[str]:
        if self.check_ownership(notification.new):
            block = [self.Token.OWNERSHIP]
        else:
            block = []

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
        block = [fr"* {self.Formatter.italic('Указана максимальная скидка для клиента')}"]
        return block

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

    def construct_personal_sale_block(self, notification: parser_price_models.Notification) -> list[str]:
        block_name = notification.new.get_field_verbose_name("personal_sale")
        new_personal_sale = notification.new.personal_sale
        old_personal_sale = notification.old.personal_sale
        if new_personal_sale is None:
            new_personal_sale = 0
        if old_personal_sale is None:
            old_personal_sale = 0

        if new_personal_sale != old_personal_sale:
            if new_personal_sale is not None and old_personal_sale is not None:
                if new_personal_sale > old_personal_sale:
                    emoji = self.Token.UP
                else:
                    emoji = self.Token.DOWN

                block = [
                    f"{self.Token.CHANGES_PERSONAL_SALE} {block_name} изменилась",
                    f"{emoji} {block_name}: {new_personal_sale} <==="
                    f" {self.Formatter.strikethrough(old_personal_sale)}"
                    f" {self.Formatter.changes_repr(new_personal_sale, old_personal_sale)} %"
                ]
            else:
                block = [
                    f"{self.Token.CHANGES_PERSONAL_SALE} {block_name} изменилась",
                    f"{self.Token.NO_CHANGES} {block_name}: {new_personal_sale} <==="
                    f" {self.Formatter.strikethrough(old_personal_sale)} %"
                ]
        else:
            block = [f"{self.Token.NO_CHANGES} {block_name}: {new_personal_sale}"]

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

    def construct_no_personal_sale_block(self) -> list[str]:
        return [f"{self.Token.NO_PERSONAL_SALE} Скидка постоянного покупателя отсутствует"]

    def notify(self, notifications: list[parser_price_models.Notification]) -> None:
        limit = self.settings.API_MESSAGES_PER_SECOND_LIMIT // self.settings.PYTEST_XDIST_WORKER_COUNT
        for notification_batch in [notifications[x:x + limit] for x in range(0, len(notifications), limit)]:
            for notification in notification_batch:
                try:
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
                    if (platform.node() == self.settings.secrets.developer.pc_name and
                            notification.new.item.user == core_models.ParserUser.get_customer()):
                        notification.new.item.user = core_models.ParserUser.get_developer()
                    if platform.node() != self.settings.secrets.developer.pc_name:
                        self.send_message(
                            notification.new.item.user.telegram_chat_id,
                            text,
                            self.ParseMode.MARKDOWN,
                            disable_web_page_preview = True
                        )
                    else:
                        try:
                            # дублируется сообщение для другого пользователя по просьбе заказчика
                            if notification.new.item.user == core_models.ParserUser.get_customer():
                                self.send_message(
                                    5250931949,
                                    text,
                                    self.ParseMode.MARKDOWN,
                                    disable_web_page_preview = True
                                )
                        except ApiTelegramException as error:
                            self.logger.info(str(error))
                        self.send_message(
                            core_models.ParserUser.get_developer().telegram_chat_id,
                            text,
                            self.ParseMode.MARKDOWN,
                            disable_web_page_preview = True
                        )
                    notification.delivered = True
                except Exception as error:
                    notification.delivered = False
                    notification.error = str(error)
                    raise error
                finally:
                    notification.save()
            time.sleep(1)

    send_message = telebot.TeleBot.send_message


# todo: перейти с поллинга на вебхук
class Bot(NotifierMixin, telebot.TeleBot):
    # общие команды
    common_commands = [
        types.BotCommand("parse_item", "Получить цену товара"),
        types.BotCommand("get_chat_id", "Получить chat.id"),
    ]
    # команды для пользователей
    user_commands = [
        types.BotCommand("start", "Регистрация"),
        types.BotCommand("add_item", "Добавить товар в отслеживаемые"),
        types.BotCommand("remove_item", "Убрать товар из отслеживаемых"),
        types.BotCommand("get_all_items", "Получить список всех отслеживаемых товаров"),
        types.BotCommand("check_subscriptions", "Проверить необходимые подписки"),
    ]
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

    def __init__(self, token: str = None):
        if token is None:
            token = self.settings.secrets.bot_telegram.token

        super().__init__(token)

    def register_handlers(self) -> None:
        # общие команды
        self.message_handler(commands = ["parse_item"])(self.parse_item)
        self.message_handler(commands = ["get_chat_id"])(self.get_chat_id)

        # команды для пользователей
        self.message_handler(commands = ["start"])(self.start)
        self.message_handler(commands = ["add_item"])(self.add_item)
        self.message_handler(commands = ["remove_item"])(self.remove_item)
        self.message_handler(commands = ["get_all_items"])(self.get_all_items)
        self.message_handler(commands = ["check_subscriptions"])(self.check_subscriptions)

        # команды для заказчика
        self.message_handler(commands = ["send_to_users"])(self.send_to_users)
        self.callback_query_handler(
            lambda callback: callback.data.startswith("send_to_users")
        )(self.send_to_users_callback_send)
        self.callback_query_handler(
            lambda callback: callback.data.startswith("cancel_send_to_users")
        )(self.send_to_users_callback_cancel)

        # команды для разработчика
        self.message_handler(commands = ["register_as_developer"])(self.register_as_developer)
        self.message_handler(commands = ["remove_user"])(self.remove_user)
        self.message_handler(commands = ["reset_command_list"])(self.reset_command_list)

        # проверка отписки от каналов
        self.chat_member_handler()(self.notify_unsubscriber)

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
                telegram_chat_id = message.chat.id
            )
            user.save()
            text = [
                SUBSCRIPTION_TEXT,
                "",
                "После того, как подпишитесь, сможете отслеживать изменения цен и СПП.",
                "",
                f"На данный момент вы можете отслеживать до {self.settings.MAX_USER_ITEMS} товаров."
            ]
            not_subscribed = self.get_needed_subscriptions(user)
            reply_markup = types.InlineKeyboardMarkup([self.construct_subscription_buttons(not_subscribed)])

        self.send_message(
            user.telegram_chat_id,
            self.Formatter.join(text),
            self.ParseMode.MARKDOWN,
            reply_markup = reply_markup
        )

    @staticmethod
    def subscription_filter(function: Callable) -> Callable:
        def wrapper(self: "Bot", message: types.Message, *args, **kwargs) -> Any:
            user = self.get_parser_user(message.from_user)
            not_subscribed = self.get_needed_subscriptions(user)
            reply_markup = types.InlineKeyboardMarkup([self.construct_subscription_buttons(not_subscribed)])

            if (user != core_models.ParserUser.get_customer() and user != core_models.ParserUser.get_developer()
                    and len(not_subscribed) > 0):
                self.send_message(
                    user.telegram_chat_id,
                    self.Formatter.join([SUBSCRIPTION_TEXT]),
                    self.ParseMode.MARKDOWN,
                    reply_markup = reply_markup
                )
            else:
                return function(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def customer_filter(function: Callable) -> Callable:
        def wrapper(self: "Bot", message: types.Message, *args, **kwargs) -> Any:
            user = self.get_parser_user(message.from_user)

            if user != core_models.ParserUser.get_customer() and user != core_models.ParserUser.get_developer():
                self.send_message(
                    user.telegram_chat_id,
                    self.Formatter.join(["Только заказчик может пользоваться данной командой."]),
                    self.ParseMode.MARKDOWN
                )
            else:
                return function(self, message, *args, **kwargs)

        return wrapper

    @staticmethod
    def developer_filter(function: Callable) -> Callable:
        def wrapper(self: "Bot", message: types.Message, *args, **kwargs) -> Any:
            user = self.get_parser_user(message.from_user)

            if user != core_models.ParserUser.get_developer():
                self.send_message(
                    user.telegram_chat_id,
                    self.Formatter.join(["Только разработчик может пользоваться данной командой."]),
                    self.ParseMode.MARKDOWN
                )
            else:
                return function(self, message, *args, **kwargs)

        return wrapper

    @subscription_filter
    def get_chat_id(self, message: types.Message) -> None:
        self.send_message(
            message.chat.id,
            self.Formatter.join([self.Formatter.copyable(message.chat.id)]),
            self.ParseMode.MARKDOWN
        )

    @developer_filter
    def remove_user(self, message: types.Message) -> None:
        user = self.get_parser_user(message.from_user)
        items = parser_price_models.Item.objects.filter(user = user)
        item_ids = list(items.values_list("id", flat = True))
        prices = parser_price_models.Price.objects.filter(item_id__in = item_ids)
        prices.delete()
        items.delete()
        user.delete()

        self.send_message(message.chat.id, "Вы были удалены из БД бота.")

    # todo: переписать, чтобы регистрировал после добавления в БД
    def register_as_developer(self, message: types.Message) -> None:
        developer = core_models.ParserUser.get_developer()
        developer.telegram_user_id = message.from_user.id
        developer.telegram_chat_id = message.chat.id
        developer.save()
        self.set_command_list_developer()
        self.send_message(
            developer.telegram_chat_id,
            "Вы зарегистрированы как разработчик"
        )

    @developer_filter
    def reset_command_list(self, message: types.Message) -> None:
        user = self.get_parser_user(message.from_user)
        scope = types.BotCommandScopeChat(user.telegram_chat_id)
        self.delete_my_commands(scope)
        self.send_message(user.telegram_chat_id, "Ваш список команд сброшен.")

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

    def notify_unsubscriber(self, update: types.ChatMemberUpdated) -> None:
        if update.new_chat_member.status in self.settings.CHANNEL_NON_SUBSCRIPTION_STATUSES \
                and (user := self.get_parser_user(update.from_user)) is not None:
            text = [SUBSCRIPTION_TEXT]
            not_subscribed = self.get_needed_subscriptions(user)
            reply_markup = types.InlineKeyboardMarkup([self.construct_subscription_buttons(not_subscribed)])
            if platform.node() != self.settings.secrets.developer.pc_name:
                self.send_message(
                    user.telegram_chat_id,
                    self.Formatter.join(text),
                    self.ParseMode.MARKDOWN,
                    reply_markup = reply_markup
                )

    @staticmethod
    def construct_subscription_buttons(not_subscribed: Subscriptions) -> list[types.InlineKeyboardButton]:
        buttons = []
        for _, data in not_subscribed.items():
            buttons.append(types.InlineKeyboardButton(data[1], url = data[0]))
        return buttons

    @subscription_filter
    def parse_item(self, message: types.Message) -> None:
        user = self.get_parser_user(message.from_user)
        self.register_next_step_handler(message, self.parse_item_step_vendor_code, user)
        self.send_message(
            user.telegram_chat_id,
            "Введите артикул товара."
        )

    def parse_item_step_vendor_code(self, message: types.Message, user: core_models.ParserUser) -> None:
        vendor_code = int(message.text)
        prices, errors = parsing.parse_prices([vendor_code], self.wildberries.dest, self.wildberries.regions)
        price = prices[vendor_code]
        if vendor_code in errors:
            raise errors[vendor_code]

        if price["personal_sale"] is None:
            price["personal_sale"] = 0

        block = self.construct_header(
            price["category_name"],
            vendor_code,
            price["name_site"],
            None,
            parser_price_models.Item(vendor_code = vendor_code).link
        )
        block.extend(
            [
                "",
                f"{self.Token.NO_CHANGES} {parser_price_models.Price.get_field_verbose_name('price')}:"
                f" {price['price']}",
                f"{self.Token.NO_CHANGES} {parser_price_models.Price.get_field_verbose_name('final_price')}:"
                f" {price['final_price']}",
                f"{self.Token.NO_CHANGES} {parser_price_models.Price.get_field_verbose_name('personal_sale')}:"
                f" {price['personal_sale']}",
                ""
            ]
        )
        block.extend(self.construct_final_block())
        self.send_message(
            user.telegram_chat_id,
            self.Formatter.join(block),
            self.ParseMode.MARKDOWN
        )

    @subscription_filter
    def add_item(self, message: types.Message) -> None:
        user = self.get_parser_user(message.from_user)

        current_items = parser_price_models.Item.objects.filter(user = user)
        if len(current_items) > self.settings.MAX_USER_ITEMS:
            self.send_message(
                user.telegram_chat_id,
                self.Formatter.join(
                    [
                        f"У Вас уже отслеживается товаров: {len(current_items)}.",
                        "Удалите лишние товары, чтобы добавить новый."
                    ]
                ),
                self.ParseMode.MARKDOWN
            )
        else:
            new_item = parser_price_models.Item(user = user)
            self.register_next_step_handler(message, self.add_item_step_name, user, new_item)
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

    @subscription_filter
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

    @subscription_filter
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

    @customer_filter
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
        reply_markup = types.InlineKeyboardMarkup([[send_button, cancel_button]])
        self.send_message(
            user.telegram_chat_id,
            "Сообщение выше отображается также, как будет отображаться пользователям.",
            reply_markup = reply_markup
        )

    def send_to_users_callback_send(self, callback: types.CallbackQuery) -> None:
        message_to_send = bot_telegram_models.SendToUsers.objects.get(id = callback.data.split(':')[-1])

        users = list(core_models.ParserUser.objects.exclude(username = message_to_send.user))
        if platform.node() != self.settings.secrets.developer.pc_name:
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

    @subscription_filter
    def check_subscriptions(self, message: types.Message) -> None:
        user = self.get_parser_user(message.from_user)
        self.send_message(
            user.telegram_chat_id,
            self.Formatter.join(["Вы подписаны на все необходимые каналы."]),
            self.ParseMode.MARKDOWN
        )
