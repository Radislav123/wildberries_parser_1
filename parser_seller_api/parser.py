import requests

import core.service.parsing
from core import models as core_models, parser as parser_core
from core.service import parsing
from parser_seller_api import models, settings


class SellerApiRequestException(Exception):
    pass


class Parser(parser_core.Parser):
    settings = settings.Settings()
    parsing_type = core_models.Parsing.Type.SELLER_API

    # https://openapi.wb.ru/prices/api/ru/#tag/Sostoyaniya-zagruzok/paths/~1api~1v2~1buffer~1goods~1task/get
    def make_request(self, user: core_models.ParserUser, offset: int) -> list[dict[str, int | str | list[dict]]]:
        scheme = "https"
        domain = "discounts-prices-api.wb.ru"
        path = "api/v2/list/goods/filter"
        url = f"{scheme}://{domain}/{path}"

        headers = {"Authorization": user.seller_api_token}
        data_limit = 1000
        params = {
            "limit": data_limit,
            "offset": offset
        }
        response = requests.get(url, params, headers = headers)

        if response.status_code != 200:
            error_text = f"{response}\n"
            error_text += response.text
            raise SellerApiRequestException(response.text)
        data: list[dict] = response.json()["data"]["listGoods"]
        if len(data) == data_limit:
            additional_data = self.make_request(user, offset + data_limit)
            data.extend(additional_data)

        return data

    def run(self) -> dict[int, core.service.parsing.ParsedPrice]:
        users = core_models.ParserUser.objects.all()
        items = []
        not_parsed = {}
        not_valid_token_users = []
        old_items = list(models.Item.objects.all().prefetch_related("category"))
        old_items_categories = {x.vendor_code: x.category for x in old_items}

        for user in users:
            try:
                if user.seller_api_token:
                    user_items = [
                        models.Item(
                            vendor_code = x["nmID"],
                            user = user,
                            # todo: тут скорее всего нужно менять логику, так как завязываться на первом размере - неправильно
                            price = x["sizes"][0]["price"],
                            discount = x["discount"]
                        ) for x in self.make_request(user, 0)
                    ]
                    items.extend(user_items)
                else:
                    not_parsed[user] = None
            except Exception as error:
                not_parsed[user] = error
                if isinstance(error, SellerApiRequestException):
                    user.seller_api_token = None
                    not_valid_token_users.append(user)

        item_vendor_codes = list(x.vendor_code for x in items)
        prices, _ = parsing.parse_prices(
            item_vendor_codes,
            self.settings.MOSCOW_CITY_DICT["dest"],
            old_items_categories,
            True,
            {x.vendor_code: x for x in items}
        )

        for item in items:
            try:
                price = prices[item.vendor_code]
                item.category = price.category
                item.name_site = price.name_site
                item.personal_discount = price.personal_discount
                item.final_price = price.final_price
            except KeyError:
                pass

        # удаление дублирующихся товаров и товаров с отрицательным СПП
        items = {x.vendor_code: x for x in items if x.personal_discount is None or x.personal_discount >= 0}

        models.Item.objects.filter(id__in = [x.id for x in old_items]).delete()
        models.Item.objects.bulk_create(list(items.values()))
        models.Item.copy_to_history(list(items.values()))

        if len(not_valid_token_users) > 0 and len(not_valid_token_users) / len(users) < 0.5:
            core_models.ParserUser.objects.bulk_update(not_valid_token_users, ["seller_api_token"])
        self.logger.info(f"Not parsed users: {len(not_parsed)}.")

        return prices
