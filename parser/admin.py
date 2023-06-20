import datetime
import re
import sys
from io import BytesIO
from typing import Callable

import django.template.response
import xlsxwriter
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models as django_models
from django.http import HttpRequest, HttpResponse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from parser import settings
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

    prepared_field_names = []
    for field_name in admin_model.addition_field_names:
        if "movement" in field_name:
            prepared_field_names.append("")
        else:
            prepared_field_names.append(field_name)
    # {name: column width}
    # noinspection PyProtectedMember
    header = [
                 models.Item._meta.get_field("vendor_code").verbose_name,
                 models.Item._meta.get_field("name").verbose_name,
                 models.Keyword._meta.get_field("value").verbose_name,
                 models.Position._meta.get_field("city").verbose_name
             ] + prepared_field_names
    for row_number, column_name in enumerate(header):
        sheet.write(1, row_number, column_name)
    for row_number, data in enumerate(queryset, 2):
        data: admin_model.model
        sheet.write(row_number, 0, data.keyword.item.vendor_code)
        sheet.write(row_number, 1, data.keyword.item.name)
        sheet.write(row_number, 2, data.keyword.value)
        sheet.write(row_number, 3, data.city)
        for column_number, additional_field in enumerate(admin_model.addition_field_names, 4):
            field_data = getattr(data, additional_field)()
            if type(field_data) is SafeString:
                field_data = re.search("<span[^>]*>(.+)</span[^>]*>", field_data).group(1)
            sheet.write(row_number, column_number, field_data)
    sheet.autofit()

    comments = models.DateComment.objects.all()
    for column_number, date in zip(range(4, len(admin_model.addition_dates), 2), admin_model.addition_dates):
        try:
            comment = comments.get(date = date)
            sheet.write(0, column_number, comment.text)
        except ObjectDoesNotExist:
            pass

    book.close()

    stream.seek(0)
    response = HttpResponse(stream.read(), content_type = settings.DOWNLOAD_EXCEL_CONTENT_TYPE)
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
                 models.Item._meta.get_field("name").verbose_name,
                 models.Price._meta.get_field("reviews_amount").verbose_name,
             ] + admin_model.date_field_names
    for row_number, column_name in enumerate(header):
        sheet.write(0, row_number, column_name)
    for row_number, data in enumerate(queryset, 1):
        data: admin_model.model
        sheet.write(row_number, 0, data.item.vendor_code)
        sheet.write(row_number, 1, data.item.name)
        sheet.write(row_number, 2, data.reviews_amount)
        for column_number, date_field in enumerate(admin_model.date_field_names, 3):
            sheet.write(row_number, column_number, getattr(data, date_field)())
    sheet.autofit()
    book.close()

    stream.seek(0)
    response = HttpResponse(stream.read(), content_type = settings.DOWNLOAD_EXCEL_CONTENT_TYPE)
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
    list_display = ("item", "item_name", "city", "keyword", "page_capacities", "page", "value", "parse_time")
    list_filter = ("city", "keyword__item", "keyword__item__name", "keyword")

    def item(self, obj: model) -> models.Item:
        return obj.keyword.item

    # noinspection PyProtectedMember
    item.short_description = models.Item._meta.get_field("vendor_code").verbose_name

    def item_name(self, obj: model) -> str:
        return obj.keyword.item.name

    # noinspection PyProtectedMember
    item_name.short_description = models.Item._meta.get_field("name").verbose_name

    def position(self, obj: model) -> str:
        return obj.position_repr

    # noinspection PyProtectedMember
    position.short_description = model._meta.get_field("value").verbose_name

    # todo: нужно переделать, так как после введения страницы вычисляется неверно
    def day_position(self, obj: model) -> int | None:
        return obj.day_position

    # noinspection PyProtectedMember
    day_position.short_description = "Средняя позиция за день"

    # todo: нужно переделать, так как после введения страницы вычисляется неверно
    def month_position(self, obj: model) -> int | None:
        return obj.month_position

    # noinspection PyProtectedMember
    month_position.short_description = "Средняя позиция за месяц"


class ShowPositionAdmin(ProjectAdmin):
    model = models.ShowPosition
    default_list_display = ("item", "item_name", "keyword", "city")
    list_filter = ("city", "keyword__item__name")
    addition_field_names: list[str] = []
    addition_dates: list[datetime.date] = []
    actions = (download_show_position_excel,)

    item = PositionAdmin.item
    item_name = PositionAdmin.item_name

    def __init__(self, model: models.ShowPosition, admin_site):
        super().__init__(model, admin_site)
        if not is_migration() and models.Item.objects.exists():
            self.list_display = [x for x in self.default_list_display]
            first_object = self.model.objects.order_by("parse_date").first()
            if first_object is not None:
                day_delta = (datetime.date.today() - first_object.parse_date).days + 1
                for day in range(day_delta):
                    date = (datetime.datetime.today() - datetime.timedelta(days = day)).date()
                    str_date = str(date)
                    movement_field_name = f"{str_date}_movement"
                    self.list_display.append(str_date)
                    self.list_display.append(movement_field_name)

                    def data_wrapper(inner_date: datetime.date) -> Callable:
                        def last_data(obj: models.Position) -> int | None:
                            position_object = obj.get_last_object_by_date(inner_date)
                            if position_object is not None:
                                position = getattr(position_object, "position_repr")
                            else:
                                position = None
                            return position

                        last_data.__name__ = str_date
                        return last_data

                    self.addition_field_names.append(str_date)
                    setattr(model, str_date, data_wrapper(date))

                    def movement_wrapper(inner_date: datetime.date) -> Callable:
                        def movement(obj: models.Position) -> str | None:
                            current_object = obj.get_last_object_by_date(inner_date)
                            previous_object = obj.get_last_object_by_date(inner_date - datetime.timedelta(days = 1))
                            if current_object is not None and previous_object is not None and \
                                    current_object.real_position is not None and \
                                    previous_object.real_position is not None:
                                data = current_object.real_position - previous_object.real_position
                                if data > 0:
                                    string = format_html(f'<span style="color: #ef6f6f;">+{data}</span>')
                                elif data < 0:
                                    string = format_html(f'<span style="color: #6aa84f;">{data}</span>')
                                else:
                                    string = str(data)
                            else:
                                string = None
                            return string

                        movement.__name__ = movement_field_name
                        movement.short_description = ""
                        return movement

                    self.addition_field_names.append(movement_field_name)
                    setattr(model, movement_field_name, movement_wrapper(date))

                    self.addition_dates.append(date)

    def get_queryset(self, request: HttpRequest) -> django_models.QuerySet:
        queryset: django_models.QuerySet = super().get_queryset(request)
        fields_to_group_by = ("keyword", "city")
        new_queryset = queryset.order_by(*fields_to_group_by).distinct(*fields_to_group_by)
        return new_queryset

    def changelist_view(
            self,
            request: HttpRequest,
            extra_context: dict = None
    ) -> django.template.response.TemplateResponse:
        if extra_context is None:
            extra_context = {}
        extra_context["date_comments"] = []
        column_width = len(str(self.addition_dates[0]))
        comments = models.DateComment.objects.all()
        for date in self.addition_dates:
            try:
                comment = comments.get(date = date)
                string = comment.text
                if len(string) > column_width:
                    string = f"{string[:column_width]}..."
                # noinspection SpellCheckingInspection
                link = f"/admin/parser/datecomment/{comment.id}/change/"
            except ObjectDoesNotExist:
                string = "---"
                # noinspection SpellCheckingInspection
                link = f"/admin/parser/datecomment/add/?date={date}"
            # noinspection SpellCheckingInspection
            data = format_html(f'<a style="color: #5abfe1;" href="{link}">{string}</a>')
            extra_context["date_comments"].append(data)
        return super().changelist_view(request, extra_context)


class PriceAdmin(ProjectAdmin):
    model = models.Price
    list_display = ("item", "item_name", "reviews_amount", "final_price", "price", "personal_sale", "parse_time")

    def item_name(self, obj: model) -> str:
        return obj.item.name

    # noinspection PyProtectedMember
    item_name.short_description = models.Item._meta.get_field("name").verbose_name


class ShowPriceAdmin(ProjectAdmin):
    model = models.ShowPrice
    default_list_display = ("item", "item_name", "reviews_amount")
    list_filter = ("item__name",)
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
            first_object = self.model.objects.order_by("parse_date").first()
            if first_object is not None:
                day_delta = (datetime.date.today() - first_object.parse_date).days + 1
                for day in range(day_delta):
                    date = (datetime.datetime.today() - datetime.timedelta(days = day)).date()

                    def wrapper(inner_date, field_name):
                        def last_data(obj: models.Price) -> int | None:
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


class DateCommentAdmin(ProjectAdmin):
    model = models.DateComment
    list_display = ("text", "date")


def register_models():
    models_with_admin_page = ProjectAdmin.__subclasses__()

    for admin_model in models_with_admin_page:
        admin.site.register(admin_model.model, admin_model)

    for model in [x for x in models.ProjectModel.__subclasses__() if
                  x not in [y.model for y in models_with_admin_page]]:
        admin.site.register(model)


register_models()
