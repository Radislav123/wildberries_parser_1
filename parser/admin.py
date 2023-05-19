from io import BytesIO

import xlsxwriter
from django.contrib import admin
from django.http import HttpResponse

from . import models


class ProjectAdmin(admin.ModelAdmin):
    model: models.ProjectModel


# noinspection PyUnusedLocal
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
    for number, keyword in enumerate(queryset, 1):
        keyword: models.Keyword
        sheet.write(number, 0, keyword.value)
        sheet.write(number, 1, keyword.average_position())
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
    list_display = ("vendor_code", "cost", "cost_final", "personal_sale", "last_update")


class KeywordAdmin(ProjectAdmin):
    model = models.Keyword
    list_display = ("value", "average_position")
    actions = (download_excel,)


class PositionAdmin(ProjectAdmin):
    model = models.Position
    list_display = ("keyword", "value", "parse_time")


def register_models():
    models_with_admin_page = ProjectAdmin.__subclasses__()

    for admin_model in models_with_admin_page:
        admin.site.register(admin_model.model, admin_model)

    for model in [x for x in models.ProjectModel.__subclasses__() if
                  x not in [y.model for y in models_with_admin_page]]:
        admin.site.register(model)


register_models()
