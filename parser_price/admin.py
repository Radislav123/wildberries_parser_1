import abc
import datetime
from io import BytesIO
from typing import Callable

import xlsxwriter
from django.db import models as django_models
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse

from core import admin as core_admin
from parser_price import parser
from . import models as parser_price_models
from .settings import Settings


settings = Settings()


# noinspection PyUnusedLocal
def download_prepared_prices_excel(
        admin_model: "PreparedPriceAdmin",
        request: HttpRequest,
        queryset: django_models.QuerySet
) -> HttpResponse:
    model_name = f"{admin_model.model.__name__}"
    stream = BytesIO()
    book = xlsxwriter.Workbook(stream, {"remove_timezone": True})
    sheet = book.add_worksheet(model_name)

    # запись шапки
    header = [
        parser_price_models.Item.get_field_verbose_name("vendor_code"),
        parser_price_models.Item.get_field_verbose_name("name"),
        parser_price_models.Category.get_field_verbose_name("name"),
        parser_price_models.Price.get_field_verbose_name("reviews_amount"),
    ]
    today = datetime.date.today()
    date_range = [today - datetime.timedelta(x) for x in range(admin_model.settings.DOWNLOAD_HISTORY_DEPTH)]
    dynamic_field_names = [
        admin_model.model.get_dynamic_field_name(admin_model.model.get_field_verbose_name(field_name), date)
        for date in date_range
        for field_name in admin_model.settings.DYNAMIC_FIELDS_ORDER
    ]
    header.extend(dynamic_field_names)
    for row_number, column_name in enumerate(header):
        sheet.write(0, row_number, column_name)

    # запись таблицы
    for row_number, data in enumerate(queryset, 1):
        data: admin_model.model
        sheet.write(row_number, 0, data.price.item.vendor_code)
        sheet.write(row_number, 1, data.price.item.name)
        sheet.write(row_number, 2, data.price.reviews_amount)
        if data.price.item.category is not None:
            category_name = data.price.item.category.name
        else:
            category_name = None
        sheet.write(row_number, 3, category_name)
        for column_multiplier, date in enumerate(date_range):
            # 4 - сдвиг
            final_price_column_number = 4 + column_multiplier * 3 + 0
            price_column_number = 4 + column_multiplier * 3 + 1
            personal_sale_column_number = 4 + column_multiplier * 3 + 2
            sheet.write(row_number, final_price_column_number, data.final_prices[date])
            sheet.write(row_number, price_column_number, data.prices[date])
            sheet.write(row_number, personal_sale_column_number, data.personal_sales[date])
    sheet.autofit()
    book.close()

    stream.seek(0)
    response = HttpResponse(stream.read(), content_type = settings.DOWNLOAD_EXCEL_CONTENT_TYPE)
    response["Content-Disposition"] = f"attachment;filename={model_name}.xlsx"
    return response


class ParserPriceFilter(core_admin.CoreFilter, abc.ABC):
    pass


class PreparedPriceItemNameListFilter(ParserPriceFilter):
    title = parser_price_models.Item.get_field_verbose_name("name")
    parameter_name = "price__item__name"

    def lookups(self, request: HttpRequest, model_admin: "PreparedPriceAdmin") -> list[tuple[str, str]]:
        actual_keywords = parser.ParserPrice.get_price_parser_items(self.user)
        item_names = [(x, x) for x in sorted(set(y.name for y in actual_keywords))]
        return item_names

    def queryset(self, request: HttpRequest, queryset: django_models.QuerySet) -> django_models.QuerySet:
        if self.value() is not None:
            queryset = queryset.filter(price__item__name = self.value(), price__item__user = self.user)
        return queryset


class PreparedPriceActualListFilter(ParserPriceFilter):
    """Оставляет только те товары, которые сейчас прописаны в excel-файле (parser_price_data.xlsx)."""

    title = "Присутствие в excel-файле"
    parameter_name = "actual"

    def choices(self, changelist) -> list[dict]:
        choices = list(super().choices(changelist))
        choices[0]["display"] = "Только присутствующие"
        return choices

    def lookups(self, request: HttpRequest, model_admin: "PreparedPriceAdmin") -> list[tuple[bool, str]]:
        return [
            (False, "Все")
        ]

    def queryset(self, request: HttpRequest, queryset: django_models.QuerySet) -> django_models.QuerySet:
        if self.value() is None:
            actual_items = parser.ParserPrice.get_price_parser_items(self.user)
            queryset = queryset.filter(price__item__in = actual_items, price__item__user = self.user)
        return queryset


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
    list_filter = (PreparedPriceItemNameListFilter, PreparedPriceActualListFilter)
    actions = (download_prepared_prices_excel,)

    def vendor_code(self, obj: model) -> int:
        return obj.price.item.vendor_code

    vendor_code.short_description = parser_price_models.Item.get_field_verbose_name("vendor_code")

    def item_name(self, obj: model) -> str:
        return obj.price.item.name

    item_name.short_description = parser_price_models.Item.get_field_verbose_name("name")

    def category_name(self, obj: model) -> str:
        if obj.price.item.category is not None:
            category_name = obj.price.item.category.name
        else:
            category_name = None
        return category_name

    category_name.short_description = parser_price_models.Category.get_field_verbose_name("name")

    def reviews_amount(self, obj: model) -> int:
        return obj.price.reviews_amount

    reviews_amount.short_description = parser_price_models.Price.get_field_verbose_name("reviews_amount")

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
                for field_name in self.settings.DYNAMIC_FIELDS_ORDER:
                    data_function = self.wrapper(f"{field_name}s", field_name, day_delta)
                    setattr(self, data_function.__name__, data_function)
                    self.list_display.append(data_function.__name__)

    def wrapper(self, json_field_name: str, field_name: str, day_delta: int) -> Callable:
        def dynamic_field(obj: PreparedPriceAdmin.model) -> int | float:
            date = datetime.date.today() - datetime.timedelta(day_delta)
            return getattr(obj, json_field_name)[date]

        dynamic_field.__name__ = self.model.get_dynamic_field_name(field_name, day_delta)
        return dynamic_field

    def changelist_view(self, request: HttpRequest, extra_context: dict = None) -> TemplateResponse:
        # добавление контекста для выведения правильных названий колонок динамических полей
        if extra_context is None:
            extra_context = {}
        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(self.settings.SHOW_HISTORY_DEPTH)]
        field_names = [parser_price_models.Price.get_field_verbose_name(x) for x in self.settings.DYNAMIC_FIELDS_ORDER]
        extra_context["dynamic_field_names"] = [
            self.model.get_dynamic_field_name(field_name, date)
            for date in date_range
            for field_name in field_names
        ]
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request: HttpRequest) -> django_models.QuerySet:
        queryset: django_models.QuerySet = super().get_queryset(request)
        new_queryset = queryset.filter(price__item__user = self.user).order_by("price__item__name")
        return new_queryset


model_admins_to_register = [DateCommentAdmin, CategoryAdmin, ItemAdmin, PriceAdmin, PreparedPriceAdmin]
core_admin.register_models(model_admins_to_register)
