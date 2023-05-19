from datetime import datetime, timedelta

from django.db import models

from parser_project import project_settings


class ProjectModel(models.Model):
    class Meta:
        abstract = True


class Item(ProjectModel):
    # артикул
    vendor_code = models.PositiveIntegerField("Артикул", primary_key = True)
    cost = models.DecimalField("Цена", max_digits = 15, decimal_places = 2)
    cost_final = models.DecimalField("Цена после СПП", max_digits = 15, decimal_places = 2)
    # скидка постоянного покупателя
    personal_sale = models.IntegerField("СПП")
    last_update = models.DateTimeField("Время обновления", auto_now = True)

    def __str__(self) -> str:
        return str(self.vendor_code)


class Keyword(ProjectModel):
    """Ключевые слова, привязанные к конкретному товару."""

    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    value = models.CharField("Ключевая фраза")

    def __str__(self) -> str:
        return self.value

    def average_position(self) -> None | int:
        """Средняя позиция за определенный период."""

        last_month = datetime.today() - timedelta(days = project_settings.AVERAGE_POSITION_PERIOD)
        positions = [x.value for x in Position.objects.filter(keyword = self, parse_time__gte = last_month)
                     if x.value is not None]
        if len(positions) == 0:
            average_position = None
        else:
            average_position = round(sum(positions) / len(positions))
        return average_position


class Position(ProjectModel):
    """Позиция товара в поисковой выдаче по конкретному ключевому слову в определенный момент времени."""

    keyword = models.ForeignKey(Keyword, models.PROTECT, verbose_name = "Ключевая фраза")
    value = models.IntegerField("Позиция в выдаче", null = True)
    parse_time = models.DateTimeField("Время парсинга", auto_now = True)
