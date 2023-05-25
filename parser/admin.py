import datetime
import sys
from io import BytesIO

import xlsxwriter
from django.contrib import admin
from django.db import models as django_models
from django.http import HttpRequest, HttpResponse

from parser_project import project_settings
from . import models


def is_migration() -> bool:
    return "makemigrations" in sys.argv or "migrate" in sys.argv


# noinspection PyUnusedLocal
def download_show_position_excel(
        admin_model: "ShowPositionAdmin",
        request: HttpRequest,
        queryset: django_models.QuerySet
) -> HttpResponse:
    model_name = f"{admin_model.model.__name__}"
    stream = BytesIO()
    book = xlsxwriter.Workbook(stream, {"remove_timezone": True})
    sheet = book.add_worksheet(model_name)

    # {name: column width}
    # noinspection PyProtectedMember
    header = [
                 models.Item._meta.get_field("vendor_code").verbose_name,
                 models.Item._meta.get_field("name").verbose_name,
                 models.Keyword._meta.get_field("value").verbose_name,
                 models.Position._meta.get_field("city").verbose_name
             ] + admin_model.date_field_names
    for row_number, column_name in enumerate(header):
        sheet.write(0, row_number, column_name)
    for row_number, data in enumerate(queryset, 1):
        data: admin_model.model
        sheet.write(row_number, 0, data.keyword.item.vendor_code)
        sheet.write(row_number, 1, data.keyword.item.name)
        sheet.write(row_number, 2, data.keyword.value)
        sheet.write(row_number, 3, data.city)
        for column_number, date_field in enumerate(admin_model.date_field_names, 4):
            sheet.write(row_number, column_number, getattr(data, date_field)())
    sheet.autofit()
    book.close()

    stream.seek(0)
    response = HttpResponse(stream.read(), content_type = project_settings.DOWNLOAD_EXCEL_CONTENT_TYPE)
    response["Content-Disposition"] = f"attachment;filename={model_name}.xlsx"
    return response


# noinspection PyUnusedLocal
def download_show_price_excel(
        admin_model: "ShowPriceAdmin",
        request: HttpRequest,
        queryset: django_models.QuerySet
) -> HttpResponse:
    model_name = f"{admin_model.model.__name__}"
    stream = BytesIO()
    book = xlsxwriter.Workbook(stream, {"remove_timezone": True})
    sheet = book.add_worksheet(model_name)

    # {name: column width}
    # noinspection PyProtectedMember
    header = [
                 models.Item._meta.get_field("vendor_code").verbose_name,
                 models.Item._meta.get_field("name").verbose_name
             ] + admin_model.date_field_names
    for row_number, column_name in enumerate(header):
        sheet.write(0, row_number, column_name)
    for row_number, data in enumerate(queryset, 1):
        data: admin_model.model
        sheet.write(row_number, 0, data.item.vendor_code)
        sheet.write(row_number, 1, data.item.name)
        for column_number, date_field in enumerate(admin_model.date_field_names, 2):
            sheet.write(row_number, column_number, getattr(data, date_field)())
    sheet.autofit()
    book.close()

    stream.seek(0)
    response = HttpResponse(stream.read(), content_type = project_settings.DOWNLOAD_EXCEL_CONTENT_TYPE)
    response["Content-Disposition"] = f"attachment;filename={model_name}.xlsx"
    return response


class ProjectAdmin(admin.ModelAdmin):
    model: models.ProjectModel


class ItemAdmin(ProjectAdmin):
    model = models.Item
    list_display = ("name", "vendor_code")


class KeywordAdmin(ProjectAdmin):
    model = models.Keyword
    list_display = ("item", "value")


class PositionAdmin(ProjectAdmin):
    model = models.Position
    list_display = ("item", "item_name", "city", "keyword", "value", "day_position", "month_position", "parse_time")

    def item(self, obj: model) -> models.Item:
        return obj.keyword.item

    # noinspection PyProtectedMember
    item.short_description = models.Item._meta.get_field("vendor_code").verbose_name

    def item_name(self, obj: model) -> str:
        return obj.keyword.item.name

    # noinspection PyProtectedMember
    item_name.short_description = models.Item._meta.get_field("name").verbose_name

    def day_position(self, obj: model) -> int | None:
        return obj.day_position

    # noinspection PyProtectedMember
    day_position.short_description = "Средняя позиция за день"

    def month_position(self, obj: model) -> int | None:
        return obj.month_position

    # noinspection PyProtectedMember
    month_position.short_description = "Средняя позиция за месяц"


class ShowPositionAdmin(ProjectAdmin):
    model = models.ShowPosition
    default_list_display = ("item", "item_name", "keyword", "city")
    date_field_names: list[str] = []
    actions = (download_show_position_excel,)

    item = PositionAdmin.item
    item_name = PositionAdmin.item_name

    def __init__(self, model: models.ShowPosition, admin_site):
        super().__init__(model, admin_site)
        if not is_migration() and models.Item.objects.exists():
            self.list_display = [x for x in self.default_list_display]
            day_delta = (datetime.date.today() - self.model.objects.order_by("parse_date").first().parse_date).days + 1
            for day in range(day_delta):
                date = (datetime.datetime.today() - datetime.timedelta(days = day)).date()
                str_date = str(date)
                self.list_display.append(str_date)

                def wrapper(inner_date):
                    def day_position(obj: model) -> int | None:
                        filtered_objects = self.model.objects.filter(
                            keyword = obj.keyword,
                            city = obj.city,
                            parse_date = inner_date
                        )
                        if len(filtered_objects) > 0:
                            position = filtered_objects[0].day_position
                        else:
                            position = None
                        return position

                    day_position.__name__ = str_date
                    return day_position

                self.date_field_names.append(str_date)
                setattr(model, str_date, wrapper(date))

    def get_queryset(self, request: HttpRequest):
        queryset: django_models.QuerySet = super().get_queryset(request)
        fields_to_group_by = ("keyword", "city")
        new_queryset = queryset.order_by(*fields_to_group_by).distinct(*fields_to_group_by)
        return new_queryset


class PriceAdmin(ProjectAdmin):
    model = models.Price
    list_display = ("item", "final_price", "price", "personal_sale", "parse_time")


class ShowPriceAdmin(ProjectAdmin):
    model = models.ShowPrice
    default_list_display = ("item", "item_name")
    date_field_names: list[str] = []
    actions = (download_show_price_excel,)

    def item_name(self, obj: model) -> str:
        return obj.item.name

    # noinspection PyProtectedMember
    item_name.short_description = models.Item._meta.get_field("name").verbose_name

    def __init__(self, model: models.ShowPrice, admin_site):
        super().__init__(model, admin_site)
        if not is_migration() and models.Item.objects.exists():
            self.list_display = [x for x in self.default_list_display]
            obj = self.model.objects.order_by("parse_date").first()
            if obj is not None:
                day_delta = (datetime.date.today() - obj.parse_date).days + 1
                for day in range(day_delta):
                    date = (datetime.datetime.today() - datetime.timedelta(days = day)).date()

                    def wrapper(inner_date, field_name):
                        def last_data(obj: model) -> int | None:
                            price_object = self.model.objects.filter(item = obj.item, parse_date = inner_date) \
                                .order_by("parse_time").last()
                            if price_object is not None:
                                data = getattr(price_object, field_name)
                            else:
                                data = None
                            return data

                        # noinspection PyProtectedMember
                        last_data.__name__ = f"{model._meta.get_field(field_name).verbose_name} {inner_date}"
                        return last_data

                    fields = ("final_price", "price", "personal_sale")
                    for field in fields:
                        data_function = wrapper(date, field)
                        self.list_display.append(data_function.__name__)
                        self.date_field_names.append(data_function.__name__)
                        setattr(model, data_function.__name__, data_function)

    def get_queryset(self, request: HttpRequest):
        queryset: django_models.QuerySet = super().get_queryset(request)
        new_queryset = queryset.order_by("item").distinct("item")
        return new_queryset


def register_models():
    models_with_admin_page = ProjectAdmin.__subclasses__()

    for admin_model in models_with_admin_page:
        admin.site.register(admin_model.model, admin_model)

    for model in [x for x in models.ProjectModel.__subclasses__() if
                  x not in [y.model for y in models_with_admin_page]]:
        admin.site.register(model)


register_models()
