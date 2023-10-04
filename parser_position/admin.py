import abc
import csv
import datetime
import os.path
from collections import defaultdict
from io import BytesIO
from typing import Callable

import xlsxwriter
import xlsxwriter.format
from django.db import models as django_models
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from core import admin as core_admin, models as core_models
from core.service.color import AdminPanelColor, XLSXColor
from . import models as parser_position_models, parser
from .settings import Settings


settings = Settings()


def colorize_movement_admin_panel(data: int | None) -> SafeString | str | None:
    if data is not None:
        if data > 0:
            string = format_html(f'<span style="color: {AdminPanelColor.RED};">+{data}</span>')
        elif data < 0:
            string = format_html(f'<span style="color: {AdminPanelColor.GREEN};">{data}</span>')
        else:
            string = str(data)
    else:
        string = data
    return string


# noinspection PyUnusedLocal
def download_prepared_position_excel(
        admin_model: "PreparedPositionAdmin",
        request: HttpRequest,
        queryset: django_models.QuerySet[parser_position_models.PreparedPosition]
) -> HttpResponse:
    def get_movement_format(movement: int | None) -> xlsxwriter.format.Format:
        if movement not in movement_format_cache:
            if movement is None or movement == 0:
                movement_format = default_text_format
            elif movement > 0:
                movement_format = book.add_format()
                color = XLSXColor.gradient_red(-30, 0, -movement)
                movement_format.set_bg_color(color)
            else:
                movement_format = book.add_format()
                color = XLSXColor.gradient_green(-30, 0, movement)
                movement_format.set_bg_color(color)
            movement_format_cache[movement] = movement_format
        return movement_format_cache[movement]

    def get_position_repr_format(position_repr: str | None) -> xlsxwriter.format.Format:
        if position_repr not in position_repr_format_cache:
            if position_repr is None:
                position_repr_format = default_text_format
            else:
                page, position = position_repr.split('/')
                if page == "1":
                    position_repr_format = book.add_format()
                    color = XLSXColor.gradient_green(0, 100, int(position))
                    position_repr_format.set_bg_color(color)
                else:
                    position_repr_format = default_text_format
            position_repr_format_cache[position_repr] = position_repr_format
        return position_repr_format_cache[position_repr]

    model_name = f"{admin_model.model.__name__}"
    stream = BytesIO()
    book = xlsxwriter.Workbook(stream, {"remove_timezone": True})
    sheet = book.add_worksheet(model_name)
    dynamic_fields_offset = 6

    default_text_format = book.add_format()
    movement_format_cache: dict[int | None, xlsxwriter.format.Format] = {}
    position_repr_format_cache: dict[str | None, xlsxwriter.format.Format] = {}

    # запись шапки
    header = [
        parser_position_models.Item.get_field_verbose_name("vendor_code"),
        parser_position_models.Keyword.get_field_verbose_name("item_name"),
        parser_position_models.Keyword.get_field_verbose_name("value"),
        parser_position_models.Keyword.get_field_verbose_name("frequency"),
        parser_position_models.Position.get_field_verbose_name("city"),
        admin_model.model.get_field_verbose_name("long_movement"),
    ]
    today = datetime.date.today()
    date_range = [today - datetime.timedelta(x) for x in range(admin_model.settings.DOWNLOAD_HISTORY_DEPTH)]
    dynamic_field_names = [
        admin_model.dynamic_field_names[field_name](date)
        for date in date_range
        for field_name in admin_model.settings.DYNAMIC_FIELDS_ORDER
    ]
    header.extend(dynamic_field_names)
    for row_number, column_name in enumerate(header):
        sheet.write(1, row_number, column_name)

    # запись таблицы
    dynamic_fields_number = len(admin_model.settings.DYNAMIC_FIELDS_ORDER)
    for row_number, data in enumerate(queryset, 2):
        data: admin_model.model
        sheet.write(row_number, 0, data.position.keyword.item.vendor_code)
        sheet.write(row_number, 1, data.position.keyword.item_name)
        sheet.write(row_number, 2, data.position.keyword.value)
        sheet.write(row_number, 3, data.position.keyword.frequency)
        sheet.write(row_number, 4, data.position.city)
        sheet.write(row_number, 5, data.long_movement, get_movement_format(data.long_movement))
        for column_multiplier, date in enumerate(date_range):
            position_repr_column_number = dynamic_fields_offset + column_multiplier * dynamic_fields_number + 0
            movement_column_number = dynamic_fields_offset + column_multiplier * dynamic_fields_number + 1
            if date in data.position_reprs:
                sheet.write(
                    row_number,
                    position_repr_column_number,
                    data.position_reprs[date],
                    get_position_repr_format(data.position_reprs[date])
                )
                sheet.write(
                    row_number,
                    movement_column_number,
                    data.movements[date],
                    get_movement_format(data.movements[date])
                )
    sheet.autofit()

    # запись комментариев
    # todo: добавить логику выбора пользователя
    comments = parser_position_models.DateComment.objects.filter(user = core_models.ParserUser.get_customer())
    for comment_number, date in enumerate(date_range):
        comment = comments.filter(date = date).last()
        if comment is not None:
            column_number = dynamic_fields_offset + comment_number * dynamic_fields_number
            sheet.write(0, column_number, comment.text)

    book.close()

    stream.seek(0)
    response = HttpResponse(stream.read(), content_type = settings.DOWNLOAD_EXCEL_CONTENT_TYPE)
    response["Content-Disposition"] = f"attachment;filename={model_name}.xlsx"
    return response


class PreparedPositionFilter(core_admin.CoreFilter, abc.ABC):
    pass


class PreparedPositionItemNameListFilter(PreparedPositionFilter):
    """
    Предоставляет к выбору только те названия товаров, которые сейчас прописаны в excel-файле
    (parser_position.xlsx).
    """

    title = parser_position_models.Keyword.get_field_verbose_name("item_name")
    parameter_name = "keyword__item_name"

    def lookups(self, request: HttpRequest, model_admin: "PreparedPositionAdmin") -> list[tuple[str, str]]:
        actual_keywords = parser.Parser.get_position_parser_keywords()
        item_names = [(x, x) for x in sorted(set(y.item_name for y in actual_keywords))]
        return item_names

    def queryset(self, request: HttpRequest, queryset: django_models.QuerySet) -> django_models.QuerySet:
        if self.value() is not None:
            queryset = queryset.filter(
                position__keyword__item_name = self.value(),
                position__keyword__item__user = self.user
            )
        return queryset


class PreparedPositionActualListFilter(PreparedPositionFilter):
    """Оставляет только те товары, которые сейчас прописаны в excel-файле (parser_position.xlsx)."""

    title = "Присутствие в excel-файле"
    parameter_name = "actual"

    def choices(self, changelist) -> list[dict]:
        choices = list(super().choices(changelist))
        choices[0]["display"] = "Только присутствующие"
        return choices

    def lookups(self, request: HttpRequest, model_admin: "PreparedPositionAdmin") -> list[tuple[bool, str]]:
        return [
            (False, "Все")
        ]

    def queryset(self, request: HttpRequest, queryset: django_models.QuerySet) -> django_models.QuerySet:
        if self.value() is None:
            actual_keywords = parser.Parser.get_position_parser_keywords()
            queryset = queryset.filter(
                position__keyword__in = actual_keywords, position__keyword__item__user = self.user
            )
        return queryset


class ParserPositionAdmin(core_admin.CoreAdmin):
    model = parser_position_models.ParserPositionModel
    settings = settings


class DateCommentAdmin(ParserPositionAdmin):
    model = parser_position_models.DateComment


class ItemAdmin(ParserPositionAdmin):
    model = parser_position_models.Item
    list_filter = ("user",)


class KeywordAdmin(ParserPositionAdmin):
    model = parser_position_models.Keyword
    frequency_file_last_update: float | None = None
    parser_data_file_last_update: float | None = None
    list_filter = ("item_name",)

    def get_queryset(self, request: HttpRequest) -> django_models.QuerySet:
        self.update_frequency()
        queryset: django_models.QuerySet = super().get_queryset(request)
        return queryset

    @classmethod
    def update_frequency(cls) -> None:
        frequency_file_last_update = os.path.getmtime(cls.settings.FREQUENCY_DATA_PATH)
        parser_data_file_last_update = os.path.getmtime(cls.settings.PARSER_POSITION_DATA_PATH)
        if (cls.frequency_file_last_update is None or cls.parser_data_file_last_update is None or
                cls.frequency_file_last_update < frequency_file_last_update or
                cls.parser_data_file_last_update < parser_data_file_last_update):
            keywords = cls.model.objects.filter(item__user = core_models.ParserUser.get_customer())
            updated_keywords = []
            keywords_dict = defaultdict(list)
            for keyword in keywords:
                keywords_dict[keyword.value.lower()].append(keyword)

            cls.frequency_file_last_update = frequency_file_last_update
            with open(cls.settings.FREQUENCY_DATA_PATH, 'r', encoding = "utf-8") as file:
                reader = csv.reader(file)
                frequency = {row[0].lower(): int(row[1]) for row in reader}

            for keyword_value, keyword_objects in keywords_dict.items():
                if keyword_value in frequency:
                    for keyword in keyword_objects:
                        keyword.frequency = frequency[keyword_value]
                    updated_keywords.extend(keyword_objects)

            cls.model.objects.bulk_update(updated_keywords, ["frequency"])


class PositionAdmin(ParserPositionAdmin):
    model = parser_position_models.Position
    extra_list_display = {"vendor_code": "keyword"}

    @staticmethod
    def vendor_code(obj: model) -> int:
        return obj.keyword.item.vendor_code

    # todo: название не отображается - проверить
    vendor_code.short_description = parser_position_models.Item.get_field_verbose_name("vendor_code")


class PreparedPositionAdmin(core_admin.DynamicFieldAdminMixin, ParserPositionAdmin):
    model = parser_position_models.PreparedPosition
    default_list_display = ("vendor_code", "item_name", "keyword", "frequency", "city", "colorized_long_movement")
    list_filter = ("position__city", PreparedPositionItemNameListFilter, PreparedPositionActualListFilter)
    actions = (download_prepared_position_excel,)

    dynamic_field_names = {
        "position_repr": lambda x: parser_position_models.PreparedPosition.get_dynamic_field_name("", x),
        "movement": lambda _: ""
    }

    def vendor_code(self, obj: model) -> int:
        return obj.position.keyword.item.vendor_code

    vendor_code.short_description = parser_position_models.Item.get_field_verbose_name("vendor_code")

    def item_name(self, obj: model) -> str:
        return obj.position.keyword.item_name

    item_name.short_description = parser_position_models.Keyword.get_field_verbose_name("item_name")

    def keyword(self, obj: model) -> str:
        return obj.position.keyword.value

    keyword.short_description = parser_position_models.Keyword.get_field_verbose_name("value")

    def frequency(self, obj: model) -> int:
        return obj.position.keyword.frequency

    frequency.short_description = parser_position_models.Keyword.get_field_verbose_name("frequency")

    def city(self, obj: model) -> str:
        return obj.position.city

    city.short_description = parser_position_models.Position.get_field_verbose_name("city")

    def colorized_long_movement(self, obj: model) -> SafeString:
        return colorize_movement_admin_panel(obj.long_movement)

    colorized_long_movement.short_description = model.get_field_verbose_name("long_movement")

    def wrapper(self, json_field_name: str, field_name: str, day_delta: int) -> Callable:
        def dynamic_field(obj: PreparedPositionAdmin.model) -> int | float | SafeString:
            date = datetime.date.today() - datetime.timedelta(day_delta)
            field = getattr(obj, json_field_name)
            data = field.get(date, None)
            if field_name == "movement":
                data = colorize_movement_admin_panel(data)
            return data

        dynamic_field.__name__ = self.model.get_dynamic_field_name(field_name, day_delta)
        return dynamic_field

    def changelist_view(self, request: HttpRequest, extra_context: dict = None) -> TemplateResponse:
        # добавление контекста для выведения правильных названий колонок динамических полей
        if extra_context is None:
            extra_context = {}

        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(self.settings.SHOW_HISTORY_DEPTH)]

        extra_context["dynamic_field_names"] = [
            self.dynamic_field_names[field_name](date)
            for date in date_range
            for field_name in self.settings.DYNAMIC_FIELDS_ORDER
        ]

        # добавление контекста для выведения комментариев
        extra_context["date_comments"] = []
        comments = parser_position_models.DateComment.objects.filter(user = self.get_user())
        column_width = len(str(date_range[0]))
        for date in date_range:
            comment = comments.filter(date = date).last()
            if comment is not None:
                string = comment.text
                if len(string) > column_width:
                    string = f"{string[:column_width]}..."
                link = f"/admin/parser_position/datecomment/{comment.id}/change/"
            else:
                string = "---"
                link = f"/admin/parser_position/datecomment/add/?date={date}"
            # noinspection SpellCheckingInspection
            data = format_html(f'<a style="color: #5abfe1;" href="{link}">{string}</a>')
            extra_context["date_comments"].append(data)

        return super().changelist_view(request, extra_context)

    def get_queryset(self, request: HttpRequest) -> django_models.QuerySet:
        KeywordAdmin.update_frequency()
        queryset: django_models.QuerySet = super().get_queryset(request)
        filtering = {
            "position__keyword__item__user": self.get_user(),
        }
        ordering = (
            "position__keyword__item_name",
            "position__keyword__item__vendor_code",
            "position__keyword__frequency",
            "position__city",
            "position__keyword__value",
        )
        excluding = {
            "position__sold_out": True,
        }
        new_queryset = queryset.filter(**filtering).exclude(**excluding).order_by(*ordering)
        return new_queryset


model_admins_to_register = [DateCommentAdmin, ItemAdmin, KeywordAdmin, PositionAdmin, PreparedPositionAdmin]
core_admin.register_models(model_admins_to_register)
