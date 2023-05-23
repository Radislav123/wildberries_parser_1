import datetime
from io import BytesIO

import xlsxwriter
from django.contrib import admin
from django.db import models as django_models
from django.http import HttpRequest, HttpResponse

from . import models


class ProjectAdmin(admin.ModelAdmin):
    model: models.ProjectModel


# noinspection PyUnusedLocal
# todo: rewrite it
def download_excel(admin_model: ProjectAdmin, request, queryset) -> HttpResponse:
    model_name = f"{admin_model.model.__name__}"
    stream = BytesIO()
    book = xlsxwriter.Workbook(stream, {"remove_timezone": True})
    sheet = book.add_worksheet(model_name)

    # {name: column width}
    header = (
        ("Ключевая фраза", 30),
        ("Средняя позиция в выдаче", 25),
    )
    datetime_format = book.add_format({"num_format": "dd.mm.yy hh:mm:ss"})
    for number, column in enumerate(header):
        sheet.set_column(number, number, column[1])
        sheet.write(0, number, column[0])
    for number, data in enumerate(queryset, 1):
        data: models.AveragePosition
        sheet.write(number, 0, data.value)
        sheet.write(number, 1, data.average_position)
    book.close()

    stream.seek(0)
    # noinspection SpellCheckingInspection
    response = HttpResponse(
        stream.read(), content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f"attachment;filename={model_name}.xlsx"
    return response


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
    default_list_display = ("keyword", "item", "item_name", "city")

    item = PositionAdmin.item
    item_name = PositionAdmin.item_name

    def __init__(self, model: models.ShowPosition, admin_site):
        super().__init__(model, admin_site)
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

            setattr(model, str_date, wrapper(date))

    def get_queryset(self, request: HttpRequest):
        queryset: django_models.QuerySet = super().get_queryset(request)
        fields_to_group_by = ("keyword", "city")
        new_queryset = queryset.order_by(*fields_to_group_by).distinct(*fields_to_group_by)
        return new_queryset

    @staticmethod
    def dynamic_date_field(obj: model) -> int | None:
        return obj.month_position


class PriceAdmin(ProjectAdmin):
    model = models.Price
    list_display = ("item", "final_price", "price", "personal_sale", "parse_time")


# todo: remove class?
class ShowPriceAdmin(ProjectAdmin):
    model = models.ShowPrice
    list_display = ("item",)


def register_models():
    models_with_admin_page = ProjectAdmin.__subclasses__()

    for admin_model in models_with_admin_page:
        admin.site.register(admin_model.model, admin_model)

    for model in [x for x in models.ProjectModel.__subclasses__() if
                  x not in [y.model for y in models_with_admin_page]]:
        admin.site.register(model)


register_models()
