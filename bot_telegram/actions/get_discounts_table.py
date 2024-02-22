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
    description = "Получить таблицу скидок"
    callback_id = CallbackData.GET_DISCOUNTS_TABLE

    book_path = f"{base.BaseAction.settings.ACTIONS_DATA_PATH}/get_discounts_table.xlsx"
    update_time: datetime.datetime = None
    book_data: bytes = None
    file_id: str = None

    @classmethod
    @base.BaseAction.open_menu_after_action
    @subscription_filter
    @seller_api_token_filter
    def execute(cls, callback: types.CallbackQuery, bot: "Bot", user: core_models.ParserUser) -> None:
        last_parsing: core_models.Parsing = core_models.Parsing.objects.filter(
            type = core_models.Parsing.Type.SELLER_API
        ).order_by("time").last()

        if cls.file_id is None or cls.update_time is None or last_parsing.time > cls.update_time:
            with xlsxwriter.Workbook(cls.book_path) as book:
                sheet = book.add_worksheet("discounts")

                # todo: write data into sheet
                sheet.write(0, 0, 123)
                sheet.write(1, 1, "123")
                sheet.autofit()

            with open(cls.book_path, "rb") as book_file:
                cls.book_data = book_file.read()
                cls.update_time = datetime.datetime.now()

            message = bot.send_document(user.telegram_chat_id, (f"discounts_{cls.update_time}.xlsx", cls.book_data))
            cls.file_id = message.document.file_id
        else:
            bot.send_document(user.telegram_chat_id, cls.file_id)
