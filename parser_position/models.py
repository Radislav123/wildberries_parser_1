import datetime
from typing import Iterable, Self

from django.contrib.postgres.fields import ArrayField
from django.db import models

from core import models as core_models
from .settings import Settings


settings = Settings()


class ParserPositionModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class DateComment(ParserPositionModel):
    user = models.ForeignKey(core_models.ParserUser, models.PROTECT)
    text = models.TextField()
    date = models.DateField()


class Item(ParserPositionModel, core_models.Item):
    user = models.ForeignKey(core_models.ParserUser, models.PROTECT, related_name = f"{settings.APP_NAME}_user")


class Keyword(ParserPositionModel):
    """Ключевая фраза, привязанная к конкретному товару."""

    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    item_name = models.CharField("Название")
    value = models.CharField("Ключевая фраза")
    frequency = models.PositiveIntegerField("Частотность", null = True)

    def __str__(self) -> str:
        return self.value


class Position(ParserPositionModel):
    """Позиция товара в поисковой выдаче по конкретной ключевой фразе в определенный момент времени."""

    keyword = models.ForeignKey(Keyword, models.PROTECT, verbose_name = Keyword.get_field_verbose_name("value"))
    parsing = models.ForeignKey(core_models.Parsing, models.PROTECT)
    city = models.CharField("Город")
    # количества товаров на страницах
    page_capacities = ArrayField(models.PositiveIntegerField(), verbose_name = "Емкости страниц", null = True)
    page = models.PositiveIntegerField("Страница", null = True)
    position = models.PositiveIntegerField("Позиция", null = True)
    promo_page = models.PositiveIntegerField("Рекламная страница", null = True)
    promo_position = models.PositiveIntegerField("Рекламная позиция", null = True)
    sold_out = models.BooleanField("Распродано", null = True)

    @staticmethod
    def get_position_repr(page: int | None, position: int | None) -> str:
        if page is None:
            page = "-"
        if position is None:
            position = "-"
        return f"{page}/{position}"

    @property
    def position_repr(self) -> str:
        return self.get_position_repr(self.page, self.position)

    @property
    def promo_position_repr(self) -> str:
        return self.get_position_repr(self.promo_page, self.promo_position)

    @property
    def real_position(self) -> int | None:
        """Позиция с учетом страницы."""
        # 5 страница, все страницы с заполненностью по 100, 30 позиция
        # 100 * (5 - 1) + 30 = 430

        if self.page_capacities is not None and self.position is not None:
            # предполагается, что все страницы одинаковой емкости
            real_position = (self.page - 1) * self.settings.DEFAULT_PAGE_CAPACITY + self.position
        else:
            real_position = self.position
        return real_position

    @classmethod
    def get_last_by_keyword_date(cls, keyword: Keyword, date: datetime.date) -> Self:
        obj = cls.objects.filter(
            keyword = keyword,
            parsing__date = date
            # parsing__time -> id потому что у разработчика время на машине отличается от того,
            # на которой происходит парсинг
        ).order_by("id").last()
        return obj

    def movement_from(self, other: "Position") -> int:
        if other is None or other.position is None or self.position is None:
            movement = None
        else:
            movement = self.real_position - other.real_position
        return movement


class PreparedPosition(ParserPositionModel, core_models.DynamicFieldModel):
    """Таблица для отображения необходимой пользователю информации."""

    position = models.ForeignKey(Position, models.PROTECT)
    long_movement = models.IntegerField(verbose_name = f"За {settings.LONG_MOVEMENT_DELTA} дней", null = True)
    positions = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )
    position_reprs = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )
    movements = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )

    dynamic_fields = {
        "position": positions,
        "position_repr": position_reprs,
        "movement": movements
    }

    @classmethod
    def prepare(cls, keywords: Iterable[Keyword]) -> None:
        new_objects: dict[Keyword, PreparedPosition] = {
            keyword: cls(
                # parsing__time -> id потому что у разработчика время на машине отличается от того,
                # на которой происходит парсинг
                position = Position.objects.filter(keyword = keyword).order_by("id").last()
            ) for keyword in keywords
        }

        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(cls.settings.MAX_HISTORY_DEPTH + 1)]
        objects_to_save = []

        for keyword, obj in new_objects.items():
            obj.positions = {}
            obj.position_reprs = {}
            obj.movements = {}
            last_positions = [Position.get_last_by_keyword_date(obj.position.keyword, date) for date in date_range]
            for number, date in enumerate(date_range[:-1]):
                if last_positions[number] is not None:
                    obj.positions[date] = last_positions[number].real_position
                    # была реклама
                    if last_positions[number].promo_position and last_positions[number].promo_page:
                        obj.position_reprs[date] = (f"{last_positions[number].promo_position_repr}"
                                                    f" {settings.PROMO_SEPARATOR} "
                                                    f"{last_positions[number].position_repr}")
                    else:
                        obj.position_reprs[date] = last_positions[number].position_repr
                    obj.movements[date] = last_positions[number].movement_from(last_positions[number + 1])
                else:
                    obj.positions[date] = None
                    obj.position_reprs[date] = None
                    obj.movements[date] = None

            obj.prepare_long_movement()
            objects_to_save.append(obj)

        cls.objects.bulk_create(objects_to_save)
        objects_to_delete = (cls.objects.filter(position__keyword__in = keywords).
                             exclude(id__in = (x.id for x in objects_to_save)).values_list("id", flat = True))
        cls.objects.filter(id__in = objects_to_delete).delete()

    def prepare_long_movement(self) -> None:
        today = datetime.date.today()
        one_day_delta = datetime.timedelta(1)
        current_date = datetime.date.today()
        previous_date = today - datetime.timedelta(settings.LONG_MOVEMENT_DELTA - 1)

        while self.positions[current_date] is None and current_date != previous_date:
            current_date -= one_day_delta

        while self.positions[previous_date] is None and previous_date != current_date:
            previous_date += one_day_delta

        current = self.positions[current_date]
        previous = self.positions[previous_date]
        if current is not None:
            self.long_movement = current - previous
        else:
            self.long_movement = None
