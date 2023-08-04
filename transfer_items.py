# noinspection PyUnresolvedReferences
import configure_django
from parser_position import models as parser_position_models
from parser_price import models as parser_price_models


def transfer_positions():
    for item in parser_position_models.Item.objects.all():
        temp_item = parser_position_models.ItemTemp(
            vendor_code = item.vendor_code,
            user = item.user
        )
        temp_item.save()
        keywords = parser_position_models.Keyword.objects.filter(item = item)
        for keyword in keywords:
            keyword.item_temp = temp_item
            keyword.save()


def transfer_prices():
    for item in parser_price_models.Item.objects.all():
        temp_item = parser_price_models.ItemTemp(
            vendor_code = item.vendor_code,
            user = item.user,
            name = item.name,
            name_site = item.name_site,
            category = item.category
        )
        temp_item.save()
        prices = parser_price_models.Price.objects.filter(item = item)
        for price in prices:
            price.item_temp = temp_item
            price.save()


def main():
    transfer_positions()
    transfer_prices()


if __name__ == "__main__":
    main()
