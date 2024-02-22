from django.db import models

from core import models as core_models
from parser_price import models as parse_price_models
from .settings import Settings


settings = Settings()


class ParserSellerApiModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class Item(ParserSellerApiModel, core_models.Item):
    vendor_code = models.PositiveIntegerField(core_models.Item.get_field_verbose_name("vendor_code"), unique = True)
    user = models.ForeignKey(core_models.ParserUser, models.PROTECT, related_name = f"{settings.APP_NAME}_user")
    price = models.PositiveIntegerField("Цена до всех скидок")
    discount = models.PositiveIntegerField("Скидка продавца")
    category = models.ForeignKey(
        parse_price_models.Category,
        models.PROTECT,
        verbose_name = parse_price_models.Category.get_field_verbose_name("name"),
        null = True,
        related_name = f"{settings.APP_NAME}_category"
    )
    personal_discount = models.PositiveIntegerField(
        parse_price_models.Price.get_field_verbose_name("personal_discount"),
        null = True
    )

    @property
    def real_price(self) -> int:
        """Реальная цена без СПП."""
        return int(self.price * (100 - self.discount) / 100)
