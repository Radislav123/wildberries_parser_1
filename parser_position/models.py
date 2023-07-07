from django.contrib.postgres.fields import ArrayField
from django.db import models

from core import models as core_models
from .settings import Settings


settings = Settings()


class ParserPositionModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class Item(ParserPositionModel, core_models.Item):
    user = models.ForeignKey(core_models.ParserUser, models.PROTECT, related_name = f"{settings.APP_NAME}_user")


class Keyword(ParserPositionModel):
    """Ключевая фраза, привязанная к конкретному товару."""

    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    item_name = models.CharField("Название")
    value = models.CharField("Ключевая фраза")

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
    value = models.PositiveIntegerField("Позиция", null = True)

    @property
    def position_repr(self) -> str:
        page = self.page
        if page is None:
            page = "-"
        return f"{page}/{self.value}"

    @property
    def real_position(self) -> int | None:
        """Позиция с учетом страницы."""
        # 5 страница, все страницы с заполненностью по 100, 30 позиция
        # 100 * (5 - 1) + 30 = 430

        if self.page_capacities is not None and self.value is not None:
            real_position = sum(self.page_capacities[:self.page - 1]) + self.value
        else:
            real_position = self.value
        return real_position


class PreparedPosition(ParserPositionModel, core_models.DynamicFieldModel):
    """Таблица для отображения необходимой пользователю информации."""

    position = models.ForeignKey(Position, models.PROTECT)
    long_movement = models.IntegerField(verbose_name = f"За {settings.LONG_MOVEMENT_DELTA} дней")
    positions = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )
    movements = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )
    comment_ids = models.JSONField(
        encoder = core_models.DateKeyJSONFieldEncoder,
        decoder = core_models.DateKeyJsonFieldDecoder
    )

    dynamic_fields = {
        "position": positions,
        "movement": movements,
        "comment_id": comment_ids
    }

    @classmethod
    def prepare(cls) -> None:
        old_object_ids = list(cls.objects.all().values_list("id", flat = True))

        new_objects = [
            cls(
                position = Position.objects.filter()
            ) for item in Item.objects.all()
        ]

        cls.objects.filter(id__in = old_object_ids).delete()
