from bot_telegram.management.commands import telegram_bot_command
from core import models as core_models


class Command(telegram_bot_command.TelegramBotCommand):
    help = "Сбрасывает подписка пользователей"

    def handle(self, *args, **options) -> None:
        users = core_models.ParserUser.objects.all()
        for user in users:
            user.subscribed = False

        core_models.ParserUser.objects.bulk_update(users, ("subscribed",))
