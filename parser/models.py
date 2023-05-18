from django.db import models


class ProjectModel(models.Model):
    class Meta:
        abstract = True


class Item(ProjectModel):
    vendor_code = models.PositiveIntegerField("Артикул")
    position = models.IntegerField("Позиция в выдаче", null = True)
    cost = models.DecimalField("Цена", max_digits = 15, decimal_places = 2)
    cost_final = models.DecimalField("Цена после СПП", max_digits = 15, decimal_places = 2)
    # скидка постоянного покупателя
    personal_sale = models.IntegerField("СПП")
    parse_time = models.DateTimeField("Время парсинга", auto_now_add = True)

    def __str__(self) -> str:
        return str(self.vendor_code)
