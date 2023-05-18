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
        ("Артикул", 20),
        ("Позиция в выдаче", 20),
        ("Цена", 10),
        ("Цена после СПП", 20),
        ("Спп", 10),
        ("Время парсинга", 20),
    )
    datetime_format = book.add_format({"num_format": "dd.mm.yy hh:mm:ss"})
    for number, column in enumerate(header):
        sheet.set_column(number, number, column[1])
        sheet.write(0, number, column[0])
    for number, item in enumerate(queryset, 1):
        item: models.Item
        sheet.write(number, 0, item.vendor_code)
        sheet.write(number, 1, item.position)
        sheet.write(number, 2, item.cost)
        sheet.write(number, 3, item.cost_final)
        sheet.write(number, 4, item.personal_sale)
        sheet.write(number, 5, item.parse_time, datetime_format)
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
    list_display = ("vendor_code", "position", "cost", "cost_final", "personal_sale", "parse_time")
    actions = (download_excel,)


def register_models():
    admin_models = (ItemAdmin,)
    registered_models = []

    for admin_model in admin_models:
        admin.site.register(admin_model.model, admin_model)
        registered_models.append(admin_model.model)

    for model in [x for x in models.ProjectModel.__subclasses__() if x not in registered_models]:
        admin.site.register(model)


register_models()
