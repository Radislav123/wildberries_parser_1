from datetime import datetime, timedelta

from django.db import models

from parser_project import project_settings


class ProjectModel(models.Model):
    class Meta:
        abstract = True


class Item(ProjectModel):
    vendor_code = models.PositiveIntegerField("Артикул", primary_key = True)
    name = models.CharField(null = True)

    def __str__(self) -> str:
        return str(self.vendor_code)


class Keyword(ProjectModel):
    """Ключевые слова, привязанные к конкретному товару."""

    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    value = models.CharField("Ключевая фраза")

    def __str__(self) -> str:
        return self.value


class Position(ProjectModel):
    """Позиция товара в поисковой выдаче по конкретному ключевому слову в определенный момент времени."""

    # noinspection PyProtectedMember
    keyword = models.ForeignKey(Keyword, models.PROTECT, verbose_name = Keyword._meta.get_field("value").verbose_name)
    city = models.CharField("Город")
    value = models.IntegerField("Позиция в выдаче", null = True)
    parse_time = models.DateTimeField("Время парсинга", auto_now = True)


class Price(ProjectModel):
    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    price = models.DecimalField("Цена до СПП", max_digits = 15, decimal_places = 2)
    final_price = models.DecimalField("Финальная цена", max_digits = 15, decimal_places = 2)
    # скидка постоянного покупателя
    personal_sale = models.IntegerField("СПП")
    parse_time = models.DateTimeField("Время добавления", auto_now = True)

    def __str__(self) -> str:
        return str(self.item.vendor_code)


class AveragePosition(Position):
    class Meta:
        proxy = True

    @property
    def average_position(self) -> None | int:
        """Средняя позиция за определенный период."""

        last_month = datetime.today() - timedelta(days = project_settings.AVERAGE_POSITION_PERIOD)
        # todo: rewrite it
        positions = [x.value for x in Position.objects.filter(keyword = self.keyword, parse_time__gte = last_month)
                     if x.value is not None]
        if len(positions) == 0:
            average_position = None
        else:
            average_position = round(sum(positions) / len(positions))
        return average_position
