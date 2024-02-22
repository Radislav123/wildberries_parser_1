import datetime
from collections import defaultdict
from typing import Iterable, Self

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
        ordering = ["name"]

    name = models.CharField("Предмет")
    personal_discount = models.PositiveIntegerField("СПП", null = True)

    def __str__(self) -> str:
        return str(self.name)

    @classmethod
    def update_personal_discounts(cls) -> None:
        items = Item.objects.all()
        prices = []
        for item in items:
            try:
                price = Price.objects.filter(item = item).prefetch_related("item", "item__category").latest("id")
                if price:
                    prices.append(price)
            except Price.DoesNotExist:
                pass

        prices_by_categories = defaultdict(list)
        updating_categories = []
        for price in prices:
            prices_by_categories[price.item.category].append(price)

        for category, prices in prices_by_categories.items():
            personal_discounts = [x.personal_discount for x in prices if x.personal_discount]
            if personal_discounts:
                updating_categories.append(category)
                category.personal_discount = max(personal_discounts)

        if prices_by_categories:
            cls.objects.bulk_update(updating_categories, ["personal_discount"])


class Item(ParserPriceModel, core_models.Item):
    user = models.ForeignKey(core_models.ParserUser, models.PROTECT, related_name = f"{settings.APP_NAME}_user")
    name = models.CharField("Название", null = True)
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
    personal_discount = models.PositiveIntegerField("СПП", null = True)
    sold_out = models.BooleanField("Распродано")

    @classmethod
    def get_last_by_item_date(cls, item: Item, date: datetime.date) -> Self:
        obj = cls.objects.filter(
            item = item,
            parsing__date = date
            # parsing__time -> id потому что у разработчика часовой пояс на машине отличается от того,
            # при котором происходит парсинг
        ).order_by("id").last()
        return obj

    @classmethod
    def get_notifications(cls, news: list["Price"]) -> list["Notification"]:
        notifications: list[Notification] = []

        for new in news:
            old: Price = cls.objects.filter(item = new.item).exclude(id = new.id).order_by("id").last()
            if old is not None:
                if new.price is not None and old.price is not None:
                    price_changing = new.price - old.price
                else:
                    price_changing = 0

                if new.personal_discount is not None and old.personal_discount is not None:
                    personal_discount_changing = new.personal_discount - old.personal_discount
                else:
                    personal_discount_changing = 0

                if new.final_price is not None and old.final_price is not None:
                    final_price_changing = new.final_price - old.final_price
                else:
                    final_price_changing = 0

                if new.sold_out != old.sold_out or price_changing or personal_discount_changing or final_price_changing:
                    notifications.append(Notification(new = new, old = old))

        Notification.objects.bulk_create(notifications)

        return notifications


# todo: добавить удаление объектов через месяц после добавления (переписать clear_user_history)
class Notification(ParserPriceModel):
    new = models.ForeignKey(Price, models.PROTECT, related_name = "notification_set_new")
    old = models.ForeignKey(Price, models.PROTECT, related_name = "notification_set_old")
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
    personal_discounts = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )

    dynamic_fields = {
        "price": prices,
        "final_price": final_prices,
        "personal_discount": personal_discounts
    }

    @classmethod
    def prepare(cls, items: Iterable[Item]) -> None:
        new_objects: dict[Item, Self] = {
            # parsing__time -> id потому что у разработчика часовой пояс на машине отличается от того,
            # при котором происходит парсинг
            item: cls(price = Price.objects.filter(item = item).order_by("id").last()) for item in items
        }

        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(cls.settings.MAX_HISTORY_DEPTH)]
        objects_to_save = []

        for item, obj in new_objects.items():
            obj.prices = {}
            obj.final_prices = {}
            obj.personal_discounts = {}
            for date in date_range:
                try:
                    # вроде бы, исключение ожидается в этой строке
                    last_price = Price.get_last_by_item_date(obj.price.item, date)
                    if last_price is not None:
                        obj.prices[date] = last_price.price
                        obj.final_prices[date] = last_price.final_price
                        obj.personal_discounts[date] = last_price.personal_discount
                    else:
                        obj.prices[date] = None
                        obj.final_prices[date] = None
                        obj.personal_discounts[date] = None
                    objects_to_save.append(obj)
                except ObjectDoesNotExist:
                    pass

        cls.objects.bulk_create(objects_to_save)
        objects_to_delete = (cls.objects.filter(price__item__in = items)
                             .exclude(id__in = (x.id for x in objects_to_save)).values_list("id", flat = True))
        cls.objects.filter(id__in = objects_to_delete).delete()
