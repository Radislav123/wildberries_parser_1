import datetime
from typing import Self

from django.core.exceptions import ObjectDoesNotExist
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
    name_site = models.CharField("Название на сайте", null = True)
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
            # parsing__time -> id потому что у разработчика время на машине отличается от того,
            # на которой происходит парсинг
        ).order_by("id").last()
        return obj

    @classmethod
    def get_notifications(cls, new_prices: list["Price"]) -> list["Notification"]:
        notifications: list[Notification] = []

        for new_price in new_prices:
            new_sold_oud = new_price.price is None and new_price.final_price is None and new_price.personal_sale is None
            new_no_personal_sale = new_price.personal_sale is None

            # parsing__time -> id потому что у разработчика время на машине отличается от того,
            # на которой происходит парсинг
            old_price = cls.objects.filter(item = new_price.item).exclude(id = new_price.id).order_by("id").last()
            old_sold_oud = old_price.price is None and old_price.final_price is None and old_price.personal_sale is None
            old_no_personal_sale = old_price.personal_sale is None

            if old_price is not None:
                if new_price.price is not None and old_price.price is not None:
                    price_changing = new_price.price - old_price.price
                else:
                    price_changing = 0

                if new_price.personal_sale is not None and old_price.personal_sale is not None:
                    personal_sale_changing = new_price.personal_sale - old_price.personal_sale
                else:
                    personal_sale_changing = 0

                if (price_changing != 0 or personal_sale_changing != 0 or new_sold_oud != old_sold_oud
                        or new_no_personal_sale != old_no_personal_sale):
                    notifications.append(
                        Notification(
                            new = new_price,
                            old = old_price,
                            sold_out = new_sold_oud,
                            no_personal_sale = new_no_personal_sale
                        )
                    )
        Notification.objects.bulk_create(notifications)

        return notifications


class Notification(ParserPriceModel):
    new = models.ForeignKey(Price, models.PROTECT, related_name = "notification_set_new")
    old = models.ForeignKey(Price, models.PROTECT, related_name = "notification_set_old")
    sold_out = models.BooleanField()
    no_personal_sale = models.BooleanField()
    delivered = models.BooleanField(null = True)
    error = models.TextField(null = True)


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
    def prepare(cls, items: list[Item]) -> None:
        old_object_ids = list(cls.objects.filter(price__item__in = items).values_list("id", flat = True))

        new_objects: dict[Item, Self] = {
            # parsing__time -> id потому что у разработчика время на машине отличается от того,
            # на которой происходит парсинг
            item: cls(price = Price.objects.filter(item = item).order_by("id").last()) for item in items
        }

        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(cls.settings.MAX_HISTORY_DEPTH)]

        for item, obj in new_objects.items():
            obj.prices = {}
            obj.final_prices = {}
            obj.personal_sales = {}
            for date in date_range:
                try:
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
                except ObjectDoesNotExist:
                    if item.vendor_code in old_object_ids:
                        old_object_ids.remove(item.vendor_code)

        cls.objects.filter(id__in = old_object_ids).delete()
