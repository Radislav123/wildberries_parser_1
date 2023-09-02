import dataclasses
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
    @dataclasses.dataclass
    class Notification:
        new: "Price"
        old: "Price"
        sold_out: bool
        no_personal_sale: bool

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

    def check_for_notification(self) -> tuple[bool, bool]:
        sold_out = True
        no_personal_sale = True

        previous_prices = self.__class__.objects.filter(item = self.item).order_by("parsing__time")
        check_depth = len(previous_prices) - self.settings.NOTIFICATION_CHECK_DEPTH - 1
        if check_depth < 0:
            check_depth = 0
        previous_prices = previous_prices[check_depth:]

        if len(previous_prices) >= self.settings.NOTIFICATION_CHECK_DEPTH:
            one_before = previous_prices[0]
            previous_prices = previous_prices[1:]
        else:
            one_before = None

        for previous_price in previous_prices:
            if previous_price.personal_sale is not None:
                no_personal_sale = False
            if previous_price.price is not None:
                sold_out = False

        # не уведомлять повторно
        if sold_out and one_before and one_before.price is None:
            sold_out = False
        if no_personal_sale and one_before and one_before.personal_sale is None:
            no_personal_sale = False

        return sold_out, no_personal_sale

    @classmethod
    def get_notifications(cls, new_prices: list["Price"]) -> list[Notification]:
        notifications: list[cls.Notification] = []

        for new_price in new_prices:
            old_price = cls.objects.filter(
                item = new_price.item,
                price__isnull = False,
                personal_sale__isnull = False
            ).exclude(id = new_price.id).order_by("parsing__time").last()
            sold_oud, no_personal_sale = new_price.check_for_notification()

            old_algorithm = False
            if old_algorithm:
                if old_price is not None and not (new_price.price is None
                                                  or new_price.final_price is None or new_price.personal_sale is None):
                    if new_price.price is not None and old_price.price is not None:
                        price_changing = new_price.price - old_price.price
                    else:
                        if new_price.price is None or old_price.price is None:
                            price_changing = 0
                        else:
                            price_changing = None
                    if new_price.personal_sale is not None and old_price.personal_sale is not None:
                        personal_sale_changing = new_price.personal_sale - old_price.personal_sale
                    else:
                        if new_price.personal_sale is None or old_price.personal_sale is None:
                            personal_sale_changing = 0
                        else:
                            personal_sale_changing = None

                    if (price_changing != 0 or personal_sale_changing != 0) or (sold_oud or no_personal_sale):
                        notifications.append(cls.Notification(new_price, old_price, sold_oud, no_personal_sale))
            else:
                if new_price is not None and old_price is not None and new_price.final_price != old_price.final_price \
                        and new_price.final_price is not None and old_price.final_price is not None:
                    notifications.append(cls.Notification(new_price, old_price, sold_oud, no_personal_sale))

        return notifications


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
            item: cls(price = Price.objects.filter(item = item).order_by("parsing__time").last()) for item in items
        }

        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(cls.settings.MAX_HISTORY_DEPTH)]

        for item in new_objects:
            obj = new_objects[item]

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
