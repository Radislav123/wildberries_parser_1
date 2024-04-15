import datetime
from typing import TYPE_CHECKING

import xlsxwriter
from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from bot_telegram.filters import seller_api_token_filter, subscription_filter
from core import models as core_models
from parser_seller_api import models as seller_api_models


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class GetDiscountsTableAction(base.BaseAction):
    command = "get_discounts_table"
    description = "Получить таблицу СПП"
    _button_text = f"📊 {description}"
    callback_id = CallbackData.GET_DISCOUNTS_TABLE

    book_path = f"{base.BaseAction.settings.ACTIONS_RESOURCES_PATH}/temp_get_discounts_table.xlsx"
    update_time: datetime.datetime = None
    book_data: bytes = None
    file_id: str = None

    @classmethod
    @base.BaseAction.action_wrapper(open_menu_after_call = True)
    @subscription_filter
    @seller_api_token_filter
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        last_parsing: core_models.Parsing = core_models.Parsing.objects.filter(
            type = core_models.Parsing.Type.SELLER_API
        ).order_by("time").last()

        if cls.file_id is None or cls.update_time is None or last_parsing.time > cls.update_time:
            with xlsxwriter.Workbook(cls.book_path) as book:
                sheet = book.add_worksheet("discounts")
                title_height = 2

                sheet.write(title_height, 0, bot.link)
                discounts = seller_api_models.Item.get_discounts_table()
                categories = tuple(discounts)
                prices = tuple(discounts[categories[0]])

                for category_row, category in enumerate(categories, title_height + 1):
                    sheet.write(category_row, 0, category.name)
                for price_column, price in enumerate(prices, 1):
                    sheet.write(title_height, price_column, price)
                for row, category in enumerate(categories, title_height + 1):
                    for column, price in enumerate(prices, title_height + 1):
                        sheet.write(row, column, discounts[category][price])
                sheet.autofit()

                sheet.merge_range(0, 0, title_height - 1, 4, "Данная таблица сгенерирована ботом")

            with open(cls.book_path, "rb") as book_file:
                cls.book_data = book_file.read()
                cls.update_time = datetime.datetime.now()

            datetime_format = "%d.%m.%y"
            table_name = f"WBFAIR СПП {cls.update_time.strftime(datetime_format)}.xlsx"
            message = bot.send_document(user.telegram_chat_id, (table_name, cls.book_data))
            cls.file_id = message.document.file_id
        else:
            bot.send_document(user.telegram_chat_id, cls.file_id)
