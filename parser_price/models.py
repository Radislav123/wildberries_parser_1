import datetime
from typing import Self

from django.db import models

from core import models as core_models
from .settings import Settings


settings = Settings()


class ParserPriceModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class Category(ParserPriceModel):
    class Meta:
        verbose_name_plural = "Categories"

    name = models.CharField("Предмет")

    def __str__(self) -> str:
        return str(self.name)


class Item(ParserPriceModel, core_models.Item):

    user = models.ForeignKey(core_models.ParserUser, models.PROTECT, related_name = f"{settings.APP_NAME}_user")
    name = models.CharField("Название")
    category = models.ForeignKey(
        Category,
        models.PROTECT,
        verbose_name = Category.get_field_verbose_name("name"),
        null = True
    )


class Price(ParserPriceModel):
    item = models.ForeignKey(Item, models.PROTECT, verbose_name = Item.get_field_verbose_name("vendor_code"))
    parsing = models.ForeignKey(core_models.Parsing, models.PROTECT)
    reviews_amount = models.PositiveIntegerField("Количество отзывов")
    price = models.FloatField("Цена до СПП", null = True)
    final_price = models.FloatField("Финальная цена", null = True)
    personal_sale = models.PositiveIntegerField("СПП", null = True)

    @classmethod
    def get_last_by_item_date(cls, item: Item, date: datetime.date) -> Self:
        obj = cls.objects.filter(
            item = item,
            parsing__date = date
        ).order_by("parsing__time").last()
        return obj

    @classmethod
    def get_changed_prices(cls, new_prices: list["Price"]) -> list[tuple[Self, Self, float, int]]:
        # [(new_price, old_price, price_changing, personal_sale_changing)]
        changed = []

        for new_price in new_prices:
            old_prices = cls.objects.filter(item = new_price.item).order_by("-parsing__time")[:2][::-1]
            if len(old_prices) > 1:
                old_price = old_prices[-2]

                if new_price.final_price is not None and old_price.final_price is not None:
                    price_changing = new_price.final_price - old_price.final_price
                else:
                    price_changing = 0

                if new_price.personal_sale is not None and old_price.personal_sale is not None:
                    personal_sale_changing = new_price.personal_sale - old_price.personal_sale
                else:
                    personal_sale_changing = 0

                if price_changing != 0 or personal_sale_changing != 0 \
                        and new_price.final_price is not None and new_price.personal_sale is not None:
                    changed.append((new_price, old_price, price_changing, personal_sale_changing))

        return changed


class PreparedPrice(ParserPriceModel, core_models.DynamicFieldModel):
    """Таблица для отображения необходимой пользователю информации."""

    price = models.ForeignKey(Price, models.PROTECT)
    # {date: value}
    prices = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )
    final_prices = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )
    personal_sales = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )

    dynamic_fields = {
        "price": prices,
        "final_price": final_prices,
        "personal_sale": personal_sales
    }

    @classmethod
    def prepare(cls, user: core_models.ParserUser, items: list[Item]) -> None:
        old_object_ids = list(
            cls.objects.filter(price__item__in = items, price__item__user = user).values_list("id", flat = True)
        )

        new_objects = [
            cls(
                price = Price.objects.filter(item = item).order_by("parsing__time").last()
            ) for item in Item.objects.filter(vendor_code__in = items, user = user)
        ]

        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(cls.settings.MAX_HISTORY_DEPTH)]

        for obj in new_objects:
            obj.prices = {}
            obj.final_prices = {}
            obj.personal_sales = {}
            for date in date_range:
                last_price = Price.get_last_by_item_date(obj.price.item, date)
                if last_price is not None:
                    obj.prices[date] = last_price.price
                    obj.final_prices[date] = last_price.final_price
                    obj.personal_sales[date] = last_price.personal_sale
                else:
                    obj.prices[date] = None
                    obj.final_prices[date] = None
                    obj.personal_sales[date] = None
            obj.save()

        cls.objects.filter(id__in = old_object_ids).delete()
