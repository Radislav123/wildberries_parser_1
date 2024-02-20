from typing import TYPE_CHECKING

from telebot import types

from bot_telegram.actions import base
from bot_telegram.callback_data import CallbackData
from core import models as core_models
from core.service import parsing, validators
from parser_price import models as parser_price_models


if TYPE_CHECKING:
    from bot_telegram.bot import Bot


class ParseItemAction(base.BaseAction):
    command = "parse_item"
    description = "Получить цену товара"
    button_text = command
    callback_id = CallbackData.PARSE_ITEM

    @classmethod
    def execute(cls, bot: "Bot", user: core_models.ParserUser, callback: types.CallbackQuery) -> None:
        bot.register_next_step_handler(callback.message, cls.step_vendor_code, bot, user)
        bot.send_message(user.telegram_chat_id, "Введите артикул товара.")

    @classmethod
    def step_vendor_code(cls, message: types.Message, bot: "Bot", user: core_models.ParserUser) -> None:
        try:
            vendor_code = int(message.text)
            prices, errors = parsing.parse_prices([vendor_code], bot.wildberries.dest)
            price = prices[vendor_code]
            if vendor_code in errors:
                raise errors[vendor_code]

            block = bot.construct_header(
                price["category"].name,
                vendor_code,
                price["name_site"],
                None,
                parser_price_models.Item(vendor_code = vendor_code).link
            )
            block.append("")

            if price["sold_out"]:
                block.extend(bot.construct_sold_out_block())
            elif validators.validate_seller_api_token(user):
                if price["price"] is not None:
                    block.append(
                        f"{bot.Token.NO_CHANGES} {parser_price_models.Price.get_field_verbose_name('price')}:"
                        f" {price['price']}"
                    )

                if price["personal_sale"] is not None:
                    block.extend(
                        [
                            "",
                            (f"{bot.Token.NO_CHANGES} "
                             f"{parser_price_models.Price.get_field_verbose_name('personal_sale')}: "
                             f"{price['personal_sale']}")
                        ]
                    )
                else:
                    block.extend(["", *bot.construct_no_personal_sale_block(), ])

                block.extend(
                    [
                        "",
                        (f"{bot.Token.NO_CHANGES}"
                         f" {parser_price_models.Price.get_field_verbose_name('final_price')}: {price['final_price']}"),
                        "", *bot.construct_final_block(),
                    ]
                )
            else:
                block.extend(
                    [
                        *bot.construct_no_seller_api_token_block(),
                        "",
                        (f"{bot.Token.NO_CHANGES}"
                         f" {parser_price_models.Price.get_field_verbose_name('final_price')}: {price['final_price']}"),
                        "", *bot.construct_final_block(),
                    ]
                )

            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join(block),
                bot.ParseMode.MARKDOWN
            )
        except Exception as error:
            bot.send_message(
                user.telegram_chat_id,
                bot.Formatter.join(["Произошла ошибка. Попробуйте еще раз чуть позже."]),
                bot.ParseMode.MARKDOWN
            )
            raise error