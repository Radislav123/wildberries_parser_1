import abc
import sys
from typing import Type, Callable

from django.contrib import admin

from . import models as core_models
from .settings import Settings


settings = Settings()


# todo: remove this function?
def is_migration() -> bool:
    return "makemigrations" in sys.argv or "migrate" in sys.argv


def register_models(model_admins: list[Type["CoreAdmin"]]) -> None:
    for model_admin in model_admins:
        admin.site.register(model_admin.model, model_admin)


class CoreFilter(admin.SimpleListFilter, abc.ABC):
    """
    Предоставляет к выбору только те названия товаров, которые сейчас прописаны в excel-файле (parser_price.xlsx).
    """

    @property
    def user(self) -> core_models.ParserUser:
        # todo: добавить логику выбора пользователя
        return core_models.ParserUser.get_admin()


class CoreAdmin(admin.ModelAdmin):
    model = core_models.CoreModel
    settings = settings

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.list_display = self._list_display

    @property
    def _list_display(self) -> tuple:
        # noinspection PyProtectedMember
        return tuple(field.name for field in self.model._meta.fields)

    @property
    def user(self) -> core_models.ParserUser:
        if not is_migration():
            # todo: добавить логику выбора пользователя
            user = core_models.ParserUser.get_admin()
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


model_admins_to_register = [ParsingAdmin]
register_models(model_admins_to_register)
