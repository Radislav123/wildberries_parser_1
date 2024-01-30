from django.db import models

from core import models as core_models
from .settings import Settings


settings = Settings()


class ParserSellerApiModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class Item(ParserSellerApiModel, core_models.Item):
    vendor_code = models.PositiveIntegerField(core_models.Item.get_field_verbose_name("vendor_code"), unique = True)
    user = models.ForeignKey(core_models.ParserUser, models.PROTECT, related_name = f"{settings.APP_NAME}_user")
    price = models.PositiveIntegerField()
    sale = models.PositiveIntegerField()
