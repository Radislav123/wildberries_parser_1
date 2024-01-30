from core import admin as core_admin
from . import models as parser_seller_api_models
from .settings import Settings


settings = Settings()


class ParserSellerApiAdmin(core_admin.CoreAdmin):
    model = parser_seller_api_models.ParserSellerApiModel
    settings = settings


class ItemAdmin(ParserSellerApiAdmin):
    model = parser_seller_api_models.Item
    list_filter = ("user", "vendor_code")
    extra_list_display = {"real_price": None}


model_admins_to_register = [ItemAdmin]
core_admin.register_models(model_admins_to_register)
