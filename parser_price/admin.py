import datetime
from typing import Callable

from django.http import HttpRequest
from django.template.response import TemplateResponse

from core import admin as core_admin
from . import models as parser_price_models
from .settings import Settings


settings = Settings()


class ParserPriceAdmin(core_admin.CoreAdmin):
    model = parser_price_models.ParserPriceModel
    settings = settings


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
    default_list_display = ("vendor_code", "item_name", "category_name", "reviews_amount")

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

    def __init__(self, model: model, admin_site):
        super().__init__(model, admin_site)
        if not core_admin.is_migration():
            # добавление колонок для динамических полей
            self.list_display = [x for x in self.default_list_display]
            # day_delta - дней назад
            # 0 - сегодня
            # 1 - вчера
            # ...
            for day_delta in range(self.settings.SHOW_HISTORY_DEPTH):
                field_names = ("final_price", "price", "personal_sale")
                for field_name in field_names:
                    data_function = self.wrapper(field_name, day_delta)
                    setattr(self, data_function.__name__, data_function)
                    self.list_display.append(data_function.__name__)

    def wrapper(self, field_name: str, day_delta: int) -> Callable:
        def dynamic_field(obj: PreparedPriceAdmin.model) -> int | float:
            date = datetime.date.today() - datetime.timedelta(day_delta)
            return obj.get_dynamic_field_value(obj.get_dynamic_field_name(field_name, date))

        dynamic_field.__name__ = self.model.get_dynamic_field_name(field_name, day_delta)
        return dynamic_field

    def changelist_view(self, request: HttpRequest, extra_context: dict = None) -> TemplateResponse:
        # добавление контекста для выведения правильных названий колонок динамических полей
        if extra_context is None:
            extra_context = {}
        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(self.settings.SHOW_HISTORY_DEPTH)]
        extra_context["dynamic_field_names"] = [
            parser_price_models.PreparedPrice.get_dynamic_field_name(self.model.get_pretty_field_name(field_name), date) for date in date_range
            for field_name in ["final_price", "price", "personal_sale"]
        ]
        return super().changelist_view(request, extra_context)


model_admins_to_register = [DateCommentAdmin, CategoryAdmin, ItemAdmin, PriceAdmin, PreparedPriceAdmin]
core_admin.register_models(model_admins_to_register)
