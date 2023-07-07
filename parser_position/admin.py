from core import admin as core_admin
from . import models as parser_position_models

from .settings import Settings


settings = Settings()


class ParserPositionAdmin(core_admin.CoreAdmin):
    model = parser_position_models.ParserPositionModel
    settings = settings


class DateCommentAdmin(ParserPositionAdmin):
    model = parser_position_models.DateComment


class ItemAdmin(ParserPositionAdmin):
    model = parser_position_models.Item


class KeywordAdmin(ParserPositionAdmin):
    model = parser_position_models.Keyword


class PositionAdmin(ParserPositionAdmin):
    model = parser_position_models.Position


class PreparedPositionAdmin(ParserPositionAdmin):
    model = parser_position_models.PreparedPosition


model_admins_to_register = [DateCommentAdmin, ItemAdmin, KeywordAdmin, PositionAdmin, PreparedPositionAdmin]
core_admin.register_models(model_admins_to_register)
