from typing import Iterable

import requests

from core import models as core_models, parser as parser_core
from core.service import parsing
from parser_price import models as parser_price_models
from parser_seller_api import models, settings


class SellerApiRequestException(Exception):
    pass


class Parser(parser_core.Parser):
    settings = settings.Settings()
    parsing_type = core_models.Parsing.Type.SELLER_API

    @staticmethod
    def make_request(user: core_models.ParserUser) -> list[dict[str, int]]:
        scheme = "https"
        domain = "suppliers-api.wildberries.ru"
        path = "public/api/v1/info"
        url = f"{scheme}://{domain}/{path}"

        headers = {"Authorization": user.seller_api_token}
        response = requests.get(url, headers = headers)
        if response.status_code != 200:
            error_text = f"{response}\n"
            error_text += response.text
            raise SellerApiRequestException(response.text)
        return response.json()

    def run(self, parser_price_items: list[parser_price_models.Item]) -> None:
        users = core_models.ParserUser.objects.all()
        items = []
        not_parsed = {}
        not_valid_token_users = []
        # todo: remove all last_error lines
        last_error = None

        for user in users:
            try:
                if user.seller_api_token:
                    user_items = [
                        models.Item(
                            vendor_code = x["nmId"],
                            user = user,
                            price = x["price"],
                            discount = x["discount"]
                        ) for x in self.make_request(user)
                    ]
                    items.extend(user_items)
                else:
                    not_parsed[user] = None
            except Exception as error:
                not_parsed[user] = error
                last_error = error
                if isinstance(error, SellerApiRequestException):
                    user.seller_api_token = None
                    not_valid_token_users.append(user)

        item_vendor_codes = tuple(x.vendor_code for x in items)
        prices: dict[int, parser_price_models.Price] = {
            x.item.vendor_code: x for x in
            parser_price_models.Price.objects.filter(item__vendor_code__in = item_vendor_codes).prefetch_related("item")
        }

        not_parsed_vendor_codes = [x.vendor_code for x in items if x.vendor_code not in parser_price_items]
        not_parsed_items = models.Item.objects.filter(
            vendor_code__in = not_parsed_vendor_codes
        ).prefetch_related("category")
        items_categories = {x.vendor_code: x.category for x in not_parsed_items}
        not_parsing_items, _ = parsing.parse_prices(
            not_parsed_vendor_codes,
            self.settings.MOSCOW_CITY_DICT["dest"],
            items_categories
        )

        for item in items:
            if item.vendor_code in parser_price_items:
                item.category = parser_price_items[item.vendor_code].category
                item.name_site = parser_price_items[item.vendor_code].name_site
            elif item.vendor_code in not_parsing_items:
                item.category = not_parsing_items[item.vendor_code].category
                item.name_site = not_parsing_items[item.vendor_code].name_site
            if item.vendor_code in prices:
                item.personal_discount = prices[item.vendor_code].personal_discount
                item.final_price = prices[item.vendor_code].final_price
            elif item.vendor_code in not_parsing_items:
                item.personal_discount = not_parsing_items[item.vendor_code].personal_discount
                item.final_price = not_parsing_items[item.vendor_code].final_price

        # удаление дублирующихся товаров и товаров с отрицательным СПП
        items = tuple(
            {x.vendor_code: x for x in items if x.personal_discount is None or x.personal_discount >= 0}.values()
        )

        models.Item.objects.all().delete()
        models.Item.objects.bulk_create(items)
        models.Item.copy_to_history(items)

        if len(not_valid_token_users) > 0 and len(not_valid_token_users) / len(users) < 0.5:
            # todo:return line
            # core_models.ParserUser.objects.bulk_update(not_valid_token_users, ["seller_api_token"])
            self.logger.info(f"Deleted tokens:{len(not_valid_token_users)}")
            # todo: remove debug
            self.logger.debug(f"{[x.id for x in not_valid_token_users]}")
            # todo: remove bot
            from bot_telegram.bot import Bot

            bot = Bot()
            text = f"Deleted tokens: {len(not_valid_token_users)}\n"
            text += f"{[x.id for x in not_valid_token_users]}"
            text += str(last_error)
            bot.send_message(core_models.ParserUser.get_developer().telegram_chat_id, text)

        self.logger.info(f"Not parsed users: {len(not_parsed)}.")
