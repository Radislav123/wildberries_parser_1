from django.db import models


class ProjectModel(models.Model):
    class Meta:
        abstract = True


class Item(ProjectModel):
    vendor_code = models.PositiveIntegerField()
    # parse_time = models.DateTimeField(auto_now_add = True)
    position = models.IntegerField(null = True)
    # скидка постоянного покупателя
    personal_sale = models.IntegerField()
    cost_before_personal_sale = models.DecimalField(max_digits = 15, decimal_places = 2)
    cost_final = models.DecimalField(max_digits = 15, decimal_places = 2)

    def __str__(self) -> str:
        return str(self.vendor_code)
