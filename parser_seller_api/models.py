from collections import defaultdict
from typing import Iterable

from django.db import models

from core import models as core_models
from parser_price import models as parse_price_models
from .settings import Settings


settings = Settings()


class ParserSellerApiModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class Item(ParserSellerApiModel, core_models.Item):
    vendor_code = models.PositiveIntegerField(core_models.Item.get_field_verbose_name("vendor_code"), unique = True)
    user = models.ForeignKey(core_models.ParserUser, models.PROTECT, related_name = f"{settings.APP_NAME}_user")
    price = models.PositiveIntegerField("Цена до всех скидок")
    discount = models.PositiveIntegerField("Скидка продавца")
    name_site = models.CharField(parse_price_models.Item.get_field_verbose_name("name_site"), null = True)
    category = models.ForeignKey(
        parse_price_models.Category,
        models.PROTECT,
        verbose_name = parse_price_models.Category.get_field_verbose_name("name"),
        null = True,
        related_name = f"{settings.APP_NAME}_category"
    )
    personal_discount = models.PositiveIntegerField(
        parse_price_models.Price.get_field_verbose_name("personal_discount"),
        null = True
    )
    final_price = models.PositiveIntegerField(
        parse_price_models.Price.get_field_verbose_name("final_price"),
        null = True
    )

    @property
    def real_price(self) -> int:
        """Реальная цена без СПП."""
        return int(self.price * (100 - self.discount) / 100)

    @classmethod
    def get_discounts_table(cls) -> dict[parse_price_models.Category, dict[int, int]]:
        items: models.QuerySet[cls] = cls.objects.all().prefetch_related("category")
        items_by_categories: dict[parse_price_models.Category, list[Item]] = defaultdict(list)

        for item in items:
            items_by_categories[item.category].append(item)
        items_by_categories = {key: value for key, value in items_by_categories.items()
                               if key is not None and key.name != ""}
        items_by_categories: dict[parse_price_models.Category, dict[int, Item]] = {
            category: {
                x.price: x for x in sorted(
                    (item for item in category_items if item.final_price is not None),
                    key = lambda x: x.final_price
                ) if x.personal_discount is not None
            } for category, category_items in sorted(items_by_categories.items(), key = lambda y: y[0].name)
        }

        prices = sorted(set(price for x in items_by_categories.values() for price in x))
        discounts: dict[parse_price_models.Category, dict[int, int]] = {}
        for category, category_items in items_by_categories.items():
            discounts[category] = {
                x: items_by_categories[category][x].personal_discount if x in items_by_categories[category] else None
                for x in prices
            }
        return discounts

    @staticmethod
    def copy_to_history(items: Iterable["Item"]) -> None:
        items_history = (
            ItemHistory(
                vendor_code = item.vendor_code,
                price = item.price,
                discount = item.discount,
                real_price = item.real_price,
                personal_discount = item.personal_discount,
                name_site = item.name_site,
                category_name = item.category.name if item.category else None
            ) for item in items
        )
        ItemHistory.objects.bulk_create(items_history)


class ItemHistory(ParserSellerApiModel, core_models.Item):
    class Meta:
        verbose_name_plural = "Items histories"

    time = models.DateTimeField("Время сохранения", auto_now_add = True)
    price = models.PositiveIntegerField(Item.get_field_verbose_name("price"), null = True)
    discount = models.PositiveIntegerField(Item.get_field_verbose_name("discount"), null = True)
    real_price = models.PositiveIntegerField(parse_price_models.Price.get_field_verbose_name("price"), null = True)
    personal_discount = models.PositiveIntegerField(
        parse_price_models.Price.get_field_verbose_name("personal_discount"),
        null = True
    )
    name_site = models.CharField(parse_price_models.Item.get_field_verbose_name("name_site"), null = True)
    category_name = models.CharField(parse_price_models.Category.get_field_verbose_name("name"), null = True)

    @property
    def user(self) -> None:
        # в этой истории нет привязки к пользователю
        raise NotImplementedError()
