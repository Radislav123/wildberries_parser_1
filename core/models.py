from django.db import models


class CoreModel(models.Model):
    class Meta:
        abstract = True


class Parsing(CoreModel):
    date = models.DateField("Дата парсинга", auto_now_add = True)
    time = models.DateTimeField("Время парсинга", auto_now_add = True)


class Item(CoreModel):
    class Meta:
        abstract = True

    vendor_code = models.PositiveIntegerField("Артикул", primary_key = True)

    def __str__(self) -> str:
        return str(self.vendor_code)
