from core import admin as core_admin
from . import models as bot_telegram_models
from .settings import Settings


settings = Settings()


class BotTelegramAdmin(core_admin.CoreAdmin):
    model = bot_telegram_models.BotTelegramModel
    settings = settings


class SendToUserAdmin(BotTelegramAdmin):
    model = bot_telegram_models.SendToUsers


model_admins_to_register = [SendToUserAdmin]
core_admin.register_models(model_admins_to_register)
