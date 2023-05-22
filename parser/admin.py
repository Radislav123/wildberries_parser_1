from io import BytesIO

import xlsxwriter
from django.contrib import admin
from django.db import models
from django.http import HttpResponse

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
    list_display = ("item", "item_name", "keyword", "value", "parse_time")

    def item(self, obj: model) -> models.Item:
        return obj.keyword.item

    # noinspection PyProtectedMember
    item.short_description = models.Item._meta.get_field("vendor_code").verbose_name

    def item_name(self, obj: model) -> str:
        return obj.keyword.item.name

    # noinspection PyProtectedMember
    item_name.short_description = models.Item._meta.get_field("name").verbose_name


class PriceAdmin(ProjectAdmin):
    model = models.Price
    list_display = ("item", "final_price", "price", "personal_sale", "parse_time")


class AveragePositionAdmin(ProjectAdmin):
    model = models.AveragePosition
    list_display = ("value", "average_position")
    actions = (download_excel,)

    def average_position(self, obj: model) -> None | int:
        return obj.average_position

    # noinspection PyProtectedMember
    average_position.short_description = "Средняя позиция"


def register_models():
    models_with_admin_page = ProjectAdmin.__subclasses__()

    for admin_model in models_with_admin_page:
        admin.site.register(admin_model.model, admin_model)

    for model in [x for x in models.ProjectModel.__subclasses__() if
                  x not in [y.model for y in models_with_admin_page]]:
        admin.site.register(model)


register_models()
