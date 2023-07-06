from core import admin as core_admin
from . import models as parser_position_models

from .settings import Settings


settings = Settings()


class ParserPositionAdmin(core_admin.CoreAdmin):
    model = parser_position_models.ParserPositionModel
    settings = settings


class ItemAdmin(ParserPositionAdmin):
    model = parser_position_models.Item


class KeywordAdmin(ParserPositionAdmin):
    model = parser_position_models.Keyword


class PositionAdmin(ParserPositionAdmin):
    model = parser_position_models.Position


model_admins_to_register = [ItemAdmin, KeywordAdmin, PositionAdmin]
core_admin.register_models(model_admins_to_register)
