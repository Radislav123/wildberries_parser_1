import requests

from core import models as core_models, parser as parser_core
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

    def parse_user(self, user: core_models.ParserUser) -> None:
        items = [
            models.Item(
                vendor_code = x["nmId"],
                user = user,
                price = x["price"],
                sale = x["discount"]
            ) for x in self.make_request(user)
        ]
        models.Item.objects.bulk_create(
            items,
            update_conflicts = True,
            update_fields = ["user", "price", "sale"],
            unique_fields = ["vendor_code"]
        )

    def run(self) -> None:
        users = core_models.ParserUser.objects.all()
        not_parsed = {}
        not_valid_token_users = []

        for user in users:
            try:
                if user.seller_api_token:
                    self.parse_user(user)
                else:
                    not_parsed[user] = None
            except Exception as error:
                not_parsed[user] = error
                if isinstance(error, RequestException):
                    # todo: удалять товары из БД как неактуальные?
                    user.seller_api_token = None
                    not_valid_token_users.append(user)

        if not_valid_token_users:
            core_models.ParserUser.objects.bulk_update(not_valid_token_users, ["seller_api_token"])

        if len(not_parsed) == 1:
            self.logger.info("There is 1 not parsed user.")
        elif len(not_parsed) > 1:
            self.logger.info(f"There are {len(not_parsed)} not parsed users.")
