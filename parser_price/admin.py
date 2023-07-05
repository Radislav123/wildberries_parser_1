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


class PreparedPriceAdmin(ParserPriceAdmin):
    model = parser_price_models.PreparedPrice
    list_display = ("vendor_code", "item_name", "category_name", "reviews_amount")

    def vendor_code(self, obj: model) -> int:
        return obj.price.item.vendor_code

    # noinspection PyProtectedMember
    vendor_code.short_description = parser_price_models.Item._meta.get_field("vendor_code").verbose_name

    def item_name(self, obj: model) -> str:
        return obj.price.item.name

    # noinspection PyProtectedMember
    item_name.short_description = parser_price_models.Item._meta.get_field("name").verbose_name

    def category_name(self, obj: model) -> str:
        if obj.price.item.category is not None:
            category_name = obj.price.item.category.name
        else:
            category_name = None
        return category_name

    # noinspection PyProtectedMember
    category_name.short_description = parser_price_models.Category._meta.get_field("name").verbose_name

    def reviews_amount(self, obj: model) -> int:
        return obj.price.reviews_amount

    # noinspection PyProtectedMember
    reviews_amount.short_description = parser_price_models.Price._meta.get_field("reviews_amount").verbose_name


model_admins_to_register = [DateCommentAdmin, CategoryAdmin, ItemAdmin, PriceAdmin, PreparedPriceAdmin]
core_admin.register_models(model_admins_to_register)
