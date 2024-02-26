from core import admin as core_admin
from . import models
from .settings import Settings


settings = Settings()


class ParserSellerApiAdmin(core_admin.CoreAdmin):
    model = models.ParserSellerApiModel
    settings = settings


class ItemAdmin(ParserSellerApiAdmin):
    model = models.Item
    list_filter = ("category", "user", "vendor_code")
    extra_list_display = {"real_price": "name_site"}
    reorder_fields = {"personal_discount": "category", "final_price": "category", "name_site": "category"}


class ItemHistoryAdmin(ParserSellerApiAdmin):
    model = models.ItemHistory
    list_filter = ("category_name",)


model_admins_to_register = [ItemAdmin, ItemHistoryAdmin]
core_admin.register_models(model_admins_to_register)
