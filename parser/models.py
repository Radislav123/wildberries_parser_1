from django.db import models


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
    value = models.CharField("Ключевое слово")

    def __str__(self) -> str:
        return self.value


class Position(ProjectModel):
    """Позиция товара в поисковой выдаче по конкретному ключевому слову в определенный момент времени."""

    keyword = models.ForeignKey(Keyword, models.PROTECT, verbose_name = "Ключевое слово")
    value = models.IntegerField("Позиция в выдаче", null = True)
    parse_time = models.DateTimeField("Время парсинга", auto_now = True)
