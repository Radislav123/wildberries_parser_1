import sys
from typing import Type

from django.contrib import admin

from . import models as core_models


# todo: remove this function?
def is_migration() -> bool:
    return "makemigrations" in sys.argv or "migrate" in sys.argv


def register_models(model_admins: list[Type["CoreAdmin"]]) -> None:
    for model_admin in model_admins:
        admin.site.register(model_admin.model, model_admin)


class CoreAdmin(admin.ModelAdmin):
    model = core_models.CoreModel

    @property
    def list_display(self) -> tuple:
        # noinspection PyProtectedMember
        return tuple(field.name for field in self.model._meta.fields)


class ParsingAdmin(CoreAdmin):
    model = core_models.Parsing


model_admins_to_register = [ParsingAdmin]
register_models(model_admins_to_register)
