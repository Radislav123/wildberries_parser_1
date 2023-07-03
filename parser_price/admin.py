from core import admin as core_admin
from . import models as parser_price_models


class ParserPriceAdmin(core_admin.CoreAdmin):
    model = parser_price_models.ParserPriceModel


class DateCommentAdmin(ParserPriceAdmin):
    model = parser_price_models.DateComment


class CategoryAdmin(ParserPriceAdmin):
    model = parser_price_models.Category


class ItemAdmin(ParserPriceAdmin):
    model = parser_price_models.Item


class PriceAdmin(ParserPriceAdmin):
    model = parser_price_models.Price


model_admins_to_register = [DateCommentAdmin, CategoryAdmin, ItemAdmin, PriceAdmin]
core_admin.register_models(model_admins_to_register)
