import requests

from core import models as core_models, parser as parser_core
from core.service import parsing
from parser_price import models as parser_price_models
from . import models, settings


class RequestException(Exception):
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
            raise RequestException(response.text)
        return response.json()

    def run(self) -> None:
        users = core_models.ParserUser.objects.all()
        items = []
        not_parsed = {}
        not_valid_token_users = []

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
                if isinstance(error, RequestException):
                    user.seller_api_token = None
                    not_valid_token_users.append(user)

        item_vendor_codes = tuple(x.vendor_code for x in items)
        parser_price_items: dict[int, parser_price_models.Item] = {
            x.vendor_code: x for x in
            parser_price_models.Item.objects.filter(vendor_code__in = item_vendor_codes).prefetch_related("category")
        }
        prices: dict[int, parser_price_models.Price] = {
            x.item.vendor_code: x for x in
            parser_price_models.Price.objects.filter(
                item__vendor_code__in = item_vendor_codes
            ).prefetch_related("item").order_by("id")
        }

        not_parsing_vendor_codes = [x.vendor_code for x in items if x.vendor_code not in parser_price_items]
        not_parsing_items, _ = parsing.parse_prices(not_parsing_vendor_codes, self.settings.MOSCOW_CITY_DICT["dest"])

        for item in items:
            if item.vendor_code in parser_price_items:
                item.category = parser_price_items[item.vendor_code].category
                item.name_site = parser_price_items[item.vendor_code].name_site
            elif item.vendor_code in not_parsing_items:
                item.category = not_parsing_items[item.vendor_code]["category"]
                item.name_site = not_parsing_items[item.vendor_code]["name_site"]
            if item.vendor_code in prices:
                item.personal_discount = prices[item.vendor_code].personal_discount
            elif item.vendor_code in not_parsing_items:
                item.personal_discount = not_parsing_items[item.vendor_code]["personal_discount"]

        # удаление дублирующихся товаров
        items = tuple({x.vendor_code: x for x in items}.values())

        models.Item.objects.all().delete()
        models.Item.objects.bulk_create(items)
        models.Item.copy_to_history(items)

        if not_valid_token_users:
            core_models.ParserUser.objects.bulk_update(not_valid_token_users, ["seller_api_token"])

        if len(not_parsed) == 1:
            self.logger.info("There is 1 not parsed user.")
        elif len(not_parsed) > 1:
            self.logger.info(f"There are {len(not_parsed)} not parsed users.")
