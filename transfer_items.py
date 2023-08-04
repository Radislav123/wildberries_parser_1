# noinspection PyUnresolvedReferences
import configure_django
from parser_position import models as parser_position_models
from parser_price import models as parser_price_models


def transfer_positions():
    for item in parser_position_models.Item.objects.all():
        keywords = parser_position_models.Keyword.objects.filter(item_temp = item)
        for keyword in keywords:
            keyword.item = item
            keyword.save()


def transfer_prices():
    for item in parser_price_models.Item.objects.all():
        prices = parser_price_models.Price.objects.filter(item_temp = item)
        for price in prices:
            price.item = item
            price.save()


def main():
    transfer_positions()
    transfer_prices()


if __name__ == "__main__":
    main()
