from collections import defaultdict

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
            category: {x.price: x for x in sorted(category_items, key = lambda x: x.real_price) if x.personal_discount}
            for category, category_items in sorted(items_by_categories.items(), key = lambda y: y[0].name)
        }

        prices = sorted(set(price for x in items_by_categories.values() for price in x))
        discounts: dict[parse_price_models.Category, dict[int, int]] = {}
        for category, category_items in items_by_categories.items():
            discounts[category] = {
                x: items_by_categories[category][x].personal_discount if x in items_by_categories[category] else None
                for x in prices
            }
        return discounts
