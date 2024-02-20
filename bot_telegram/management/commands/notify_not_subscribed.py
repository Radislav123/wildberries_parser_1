import time

from bot_telegram.filters import subscription_filter
from bot_telegram.management.commands import telegram_bot_command
from core import models as core_models
from ...bot import Bot


class Command(telegram_bot_command.TelegramBotCommand):
    help = "Рассылает оповещения пользователям боты, которые не подписаны на необходимые каналы"

    def handle(self, *args, **options):
        bot = Bot()
        not_subscribed_users = core_models.ParserUser.objects.filter(subscribed = False)

        for user_batch in [not_subscribed_users[x:x + self.settings.API_MESSAGES_PER_SECOND_LIMIT]
                           for x in range(0, len(not_subscribed_users), self.settings.API_MESSAGES_PER_SECOND_LIMIT)]:
            for user in user_batch:
                if bot.check_pc(user):
                    subscription_filter(lambda *lambda_args: None)(None, bot, user, None)
            time.sleep(1)
