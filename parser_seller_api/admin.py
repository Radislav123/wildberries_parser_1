from django.contrib import admin

from core import admin as core_admin
from parser_price import models as parser_price_models
from . import models as parser_seller_api_models
from .settings import Settings


settings = Settings()


# todo: парсить категорию и сохранять в БД?
class CategoryFilter(admin.SimpleListFilter):
    title = "category"
    parameter_name = "category"

    # todo: прописать типы
    def lookups(self, request, model_admin):
        return ((x.id, x) for x in parser_price_models.Category.objects.all())

    # todo: прописать типы
    def queryset(self, request, queryset):
        if self.value() is not None:
            items = parser_price_models.Item.objects.filter(category_id = self.value())
            print(items)
            queryset = queryset.filter(vendor_code__in = (x.vendor_code for x in items))
        return queryset


class ParserSellerApiAdmin(core_admin.CoreAdmin):
    model = parser_seller_api_models.ParserSellerApiModel
    settings = settings


class ItemAdmin(ParserSellerApiAdmin):
    model = parser_seller_api_models.Item
    list_filter = (CategoryFilter, "user", "vendor_code")
    extra_list_display = {"real_price": None, "category": None, "personal_sale": None}

    @staticmethod
    def category(obj: model) -> parser_price_models.Category | None:
        items = parser_price_models.Item.objects.filter(vendor_code = obj.vendor_code)
        if items:
            item = items[0]
            category = item.category
        else:
            category = None
        return category

    @staticmethod
    def personal_sale(obj: model) -> int | None:
        items = parser_price_models.Item.objects.filter(vendor_code = obj.vendor_code)
        if items:
            item = items[0]
            price = parser_price_models.Price.objects.filter(item = item).order_by("-id")[0]
            personal_sale = price.personal_sale
        else:
            personal_sale = None
        return personal_sale


model_admins_to_register = [ItemAdmin]
core_admin.register_models(model_admins_to_register)
