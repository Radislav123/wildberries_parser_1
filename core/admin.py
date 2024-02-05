import abc
import sys
from io import BytesIO
from typing import Callable, Type

import django.forms.models
import xlsxwriter
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models as django_models
from django.http import HttpResponse

import logger
from . import models as core_models
from .settings import Settings


settings = Settings()


def is_migration() -> bool:
    return "makemigrations" in sys.argv or "migrate" in sys.argv


def register_models(model_admins: list[Type["CoreAdmin"]]) -> None:
    for model_admin in model_admins:
        admin.site.register(model_admin.model, model_admin)


def download_parser_users_excel(admin_model: "ParserUserAdmin", _, queryset: django_models.QuerySet) -> HttpResponse:
    model_name = f"{admin_model.model.__name__}"
    stream = BytesIO()
    book = xlsxwriter.Workbook(stream, {"remove_timezone": True})
    sheet = book.add_worksheet(model_name)

    # запись шапки
    header = [
        core_models.ParserUser.get_field_verbose_name("id"),
        core_models.ParserUser.get_field_verbose_name("telegram_user_id"),
    ]
    for row_number, column_name in enumerate(header):
        sheet.write(0, row_number, column_name)

    # запись таблицы
    for row_number, data in enumerate(queryset, 1):
        data: admin_model.model
        sheet.write(row_number, 0, data.id)
        sheet.write(row_number, 1, data.telegram_user_id)
    sheet.autofit()
    book.close()

    stream.seek(0)
    response = HttpResponse(stream.read(), content_type = settings.DOWNLOAD_EXCEL_CONTENT_TYPE)
    response["Content-Disposition"] = f"attachment;filename={model_name}.xlsx"
    return response


class CoreFilter(admin.SimpleListFilter, abc.ABC):
    """
    Предоставляет к выбору только те названия товаров, которые сейчас прописаны в excel-файле (parser_price.xlsx).
    """

    @property
    def user(self) -> core_models.ParserUser:
        # todo: добавить логику выбора пользователя
        return core_models.ParserUser.get_customer()


class CoreAdmin(admin.ModelAdmin):
    model = core_models.CoreModel
    settings = settings
    hidden_fields = ()
    _fieldsets = ()
    # {вставляемое_поле: поле_после_которого_вставляется}
    # {field: None} - вставится последним
    extra_list_display: dict[str, str] = {}
    not_required_fields = ()

    def __init__(self, model, admin_site):
        self.logger = logger.Logger(self.__class__.__name__)

        self.list_display = [field for field in self._list_display if field not in self.hidden_fields]
        for field, before_field in self.extra_list_display.items():
            if before_field is None:
                self.list_display.append(field)
            else:
                self.list_display.insert(self.list_display.index(before_field), field)
        self.list_display = tuple(self.list_display)
        if self.fieldsets is not None:
            self.fieldsets += self._fieldsets
        else:
            self.fieldsets = self._fieldsets

        super().__init__(model, admin_site)

    def get_form(self, request, obj = None, **kwargs) -> django.forms.models.ModelFormMetaclass:
        form = super().get_form(request, obj, **kwargs)
        for field_name in self.not_required_fields:
            form.base_fields[field_name].required = False
        return form

    @property
    def _list_display(self) -> tuple:
        # noinspection PyProtectedMember
        return tuple(field.name for field in self.model._meta.fields)

    @staticmethod
    def get_user() -> core_models.ParserUser:
        if not is_migration():
            # todo: добавить логику выбора пользователя
            user = core_models.ParserUser.get_customer()
        else:
            user = None
        return user


class DynamicFieldAdminMixin(admin.ModelAdmin):
    settings: settings
    model: core_models.DynamicFieldModel
    default_list_display: list[str]

    def __init__(self, model: core_models.DynamicFieldModel, admin_site):
        super().__init__(model, admin_site)
        if not is_migration():
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
        raise NotImplementedError()


class ParsingAdmin(CoreAdmin):
    model = core_models.Parsing
    list_filter = ("success", "type")


class ParserUserAdmin(CoreAdmin, UserAdmin):
    model = core_models.ParserUser
    hidden_fields = ("password",)
    not_required_fields = ("seller_api_token",)
    _fieldsets = (
        (
            "Telegram",
            {"fields": ("telegram_user_id", "telegram_chat_id")}
        ),
        (
            "Wildberries",
            {"fields": ("seller_api_token",)}
        )
    )
    actions = (download_parser_users_excel,)


model_admins_to_register = [ParsingAdmin, ParserUserAdmin]
register_models(model_admins_to_register)
