import datetime
import os
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
from . import models, wildberries_parser


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

    # запись шапки
    prepared_field_names = []
    for field_name in admin_model.addition_download_field_names:
        if "movement" in field_name:
            prepared_field_names.append("")
        else:
            prepared_field_names.append(field_name)
    # {name: column width}
    # noinspection PyProtectedMember
    header = [
                 models.Item._meta.get_field("vendor_code").verbose_name,
                 models.Keyword._meta.get_field("item_name").verbose_name,
                 models.Keyword._meta.get_field("value").verbose_name,
                 models.Position._meta.get_field("city").verbose_name
             ] + prepared_field_names
    for row_number, column_name in enumerate(header):
        sheet.write(1, row_number, column_name)

    # запись таблицы
    for row_number, data in enumerate(queryset, 2):
        data: admin_model.model
        sheet.write(row_number, 0, data.keyword.item.vendor_code)
        sheet.write(row_number, 1, data.keyword.item_name)
        sheet.write(row_number, 2, data.keyword.value)
        sheet.write(row_number, 3, data.city)
        for column_number, additional_field in enumerate(admin_model.addition_download_field_names, 4):
            field_data = getattr(data, additional_field)()
            if type(field_data) is SafeString:
                field_data = re.search("<span[^>]*>(.+)</span[^>]*>", field_data).group(1)
            sheet.write(row_number, column_number, field_data)
    sheet.autofit()

    # запись комментариев
    comments = models.DateComment.objects.all()
    for column_number, date in \
            zip(range(4, len(admin_model.addition_download_dates), 2), admin_model.addition_download_dates):
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

    # запись шапки
    # {name: column width}
    # noinspection PyProtectedMember
    header = [
                 models.Item._meta.get_field("vendor_code").verbose_name,
                 models.Item._meta.get_field("name_price").verbose_name,
                 models.Price._meta.get_field("reviews_amount").verbose_name,
             ] + admin_model.addition_download_field_names
    for row_number, column_name in enumerate(header):
        sheet.write(0, row_number, column_name)

    # запись таблицы
    for row_number, data in enumerate(queryset, 1):
        data: admin_model.model
        sheet.write(row_number, 0, data.item.vendor_code)
        sheet.write(row_number, 1, data.item.name_price)
        sheet.write(row_number, 2, data.reviews_amount)
        for column_number, date_field in enumerate(admin_model.addition_download_field_names, 3):
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
    list_display = ("vendor_code",)


class KeywordAdmin(ProjectAdmin):
    model = models.Keyword
    list_display = ("item", "value")


class PositionAdmin(ProjectAdmin):
    model = models.Position
    # noinspection PyProtectedMember
    list_display = tuple(field.name for field in model._meta.get_fields())
    list_filter = ("city", "keyword__item", "keyword")

    def item(self, obj: model) -> models.Item:
        return obj.keyword.item

    # noinspection PyProtectedMember
    item.short_description = models.Item._meta.get_field("vendor_code").verbose_name

    def item_name(self, obj: model) -> str:
        return obj.keyword.item_name

    # noinspection PyProtectedMember
    item_name.short_description = models.Item._meta.get_field("name").verbose_name

    def position(self, obj: model) -> str:
        return obj.position_repr

    # noinspection PyProtectedMember
    position.short_description = model._meta.get_field("value").verbose_name


class ShowPositionAdmin(ProjectAdmin):
    model = models.ShowPosition
    default_list_display = ("item", "item_name", "keyword", "city")
    list_filter = ("city", "keyword__item_name")
    addition_show_field_names: list[str] = []
    addition_show_dates: list[datetime.date] = []
    addition_download_field_names: list[str] = []
    addition_download_dates: list[datetime.date] = []
    last_names_update_time: datetime.datetime = None
    actions = (download_show_position_excel,)

    item = PositionAdmin.item
    item_name = PositionAdmin.item_name

    def __init__(self, model: model, admin_site):
        super().__init__(model, admin_site)
        if not is_migration() and models.Item.objects.exists():
            self.list_display = [x for x in self.default_list_display]
            # добавление колонок
            first_object = self.model.objects.order_by("parse_date").first()
            if first_object is not None:
                if settings.USE_HISTORY_DEPTH:
                    show_day_delta = settings.SHOW_HISTORY_DEPTH
                    download_day_delta = settings.DOWNLOAD_HISTORY_DEPTH
                else:
                    show_day_delta = (datetime.date.today() - first_object.parse_date).days + 1
                    download_day_delta = show_day_delta

                self.addition_show_field_names, self.addition_show_dates = \
                    self.get_addition_columns(show_day_delta, True)
                self.addition_download_field_names, self.addition_download_dates = \
                    self.get_addition_columns(download_day_delta, False)

    def get_addition_columns(self, day_delta: int, extend_list_display: bool) -> tuple[list[str], list[datetime.date]]:
        addition_field_names = []
        addition_dates = []
        for day in range(day_delta):
            date = (datetime.datetime.today() - datetime.timedelta(days = day)).date()
            str_date = str(date)

            position_function = self.position_wrapper(date)
            movement_function = self.movement_wrapper(date, f"{str_date}_movement")

            # добавление колонки к списку отображаемых в административной панели
            if extend_list_display:
                self.list_display.append(position_function.__name__)
                self.list_display.append(movement_function.__name__)

            # добавление позиции
            addition_field_names.append(position_function.__name__)
            setattr(self.model, position_function.__name__, position_function)

            # добавление изменения позиции
            addition_field_names.append(movement_function.__name__)
            setattr(self.model, movement_function.__name__, movement_function)

            addition_dates.append(date)

        return addition_field_names, addition_dates

    @staticmethod
    def position_wrapper(date: datetime.date) -> Callable:
        def last_position(obj: models.Position) -> int | None:
            position_object = obj.get_last_object_by_date(date)
            if position_object is not None:
                position = getattr(position_object, "position_repr")
            else:
                position = None
            return position

        last_position.__name__ = str(date)
        return last_position

    @staticmethod
    def movement_wrapper(date: datetime.date, method_name: str) -> Callable:
        def movement(obj: models.Position) -> str | None:
            """Изменение между последними результатами за указанный и предыдущий дни."""

            current_object = obj.get_last_object_by_date(date)
            previous_object = obj.get_last_object_by_date(date - datetime.timedelta(days = 1))
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

        movement.__name__ = method_name
        movement.short_description = ""
        return movement

    def get_queryset(self, request: HttpRequest) -> django_models.QuerySet:
        queryset: django_models.QuerySet = super().get_queryset(request)
        fields_to_group_by = ("keyword", "city")
        new_queryset = queryset.order_by(*fields_to_group_by).distinct(*fields_to_group_by)
        return new_queryset

    def update_object_names(self) -> None:
        """Обновляет названия товаров в соответствии с таковыми в excel-файле."""

        file_modification_time = datetime.datetime.fromtimestamp(os.path.getmtime(settings.POSITION_PARSER_DATA_PATH))
        if self.last_names_update_time is None or file_modification_time > self.last_names_update_time:
            self.last_names_update_time = datetime.datetime.now()
            wildberries_parser.WildberriesParser.get_position_parser_keywords()

    def changelist_view(
            self,
            request: HttpRequest,
            extra_context: dict = None
    ) -> django.template.response.TemplateResponse:
        # добавление контекста для выведения комментариев
        if extra_context is None:
            extra_context = {}
        extra_context["date_comments"] = []
        column_width = len(str(self.addition_show_dates[0]))
        comments = models.DateComment.objects.all()
        for date in self.addition_show_dates:
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

        self.update_object_names()
        return super().changelist_view(request, extra_context)


class PriceAdmin(ProjectAdmin):
    model = models.Price
    # noinspection PyProtectedMember
    list_display = tuple(field.name for field in model._meta.get_fields())

    def item_name(self, obj: model) -> str:
        return obj.item.name_price


class ShowPriceAdmin(ProjectAdmin):
    model = models.ShowPrice
    default_list_display = ("item", "item_name", "reviews_amount")
    list_filter = ("item__name_price",)
    addition_show_field_names: list[str] = []
    addition_show_dates: list[datetime.date] = []
    addition_download_field_names: list[str] = []
    addition_download_dates: list[datetime.date] = []
    last_names_update_time: datetime.datetime = None
    actions = (download_show_price_excel,)

    item_name = PriceAdmin.item_name

    def __init__(self, model: models.ShowPrice, admin_site):
        super().__init__(model, admin_site)
        if not is_migration() and models.Item.objects.exists():
            self.list_display = [x for x in self.default_list_display]
            # добавление колонок
            first_object = self.model.objects.order_by("parse_date").first()
            if first_object is not None:
                if settings.USE_HISTORY_DEPTH:
                    show_day_delta = settings.SHOW_HISTORY_DEPTH
                    download_day_delta = settings.DOWNLOAD_HISTORY_DEPTH
                else:
                    show_day_delta = (datetime.date.today() - first_object.parse_date).days + 1
                    download_day_delta = show_day_delta

                self.addition_show_field_names, self.addition_show_dates = \
                    self.get_addition_columns(show_day_delta, True)
                self.addition_download_field_names, self.addition_download_dates = \
                    self.get_addition_columns(download_day_delta, False)

    def get_addition_columns(self, day_delta: int, extend_list_display: bool) -> tuple[list[str], list[datetime.date]]:
        addition_field_names = []
        addition_dates = []
        for day in range(day_delta):
            date = (datetime.datetime.today() - datetime.timedelta(days = day)).date()

            fields = ("final_price", "price", "personal_sale")
            for field in fields:
                data_function = self.wrapper(date, field)

                # добавление колонки к списку отображаемых в административной панели
                if extend_list_display:
                    self.list_display.append(data_function.__name__)

                # добавление данных
                addition_field_names.append(data_function.__name__)
                setattr(self.model, data_function.__name__, data_function)

            addition_dates.append(date)

        return addition_field_names, addition_dates

    def wrapper(self, date: datetime.date, field_name: str) -> Callable:
        def last_data(obj: models.Price) -> int | None:
            price_object = obj.get_last_object_by_date(date)
            if price_object is not None:
                data = getattr(price_object, field_name)
            else:
                data = None
            return data

        # noinspection PyProtectedMember
        last_data.__name__ = f"{self.model._meta.get_field(field_name).verbose_name} {date}"
        return last_data

    def get_queryset(self, request: HttpRequest):
        queryset: django_models.QuerySet = super().get_queryset(request)
        new_queryset = queryset.order_by("item").distinct("item")
        return new_queryset

    def update_object_names(self) -> None:
        """Обновляет названия товаров в соответствии с таковыми в excel-файле."""

        file_modification_time = datetime.datetime.fromtimestamp(os.path.getmtime(settings.PRICE_PARSER_DATA_PATH))
        if self.last_names_update_time is None or file_modification_time > self.last_names_update_time:
            self.last_names_update_time = datetime.datetime.now()
            wildberries_parser.WildberriesParser.get_price_parser_items()

    def changelist_view(
            self,
            request: HttpRequest,
            extra_context: dict = None
    ) -> django.template.response.TemplateResponse:
        self.update_object_names()
        return super().changelist_view(request, extra_context)


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
