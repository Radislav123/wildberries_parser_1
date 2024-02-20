import time

from bot_telegram.filters import seller_api_token_filter
from bot_telegram.management.commands import telegram_bot_command
from core import models as core_models
from ...bot import Bot


class Command(telegram_bot_command.TelegramBotCommand):
    help = "Рассылает оповещения пользователям боты, у которых отсутствует валидный токен продавца"

    def handle(self, *args, **options):
        bot = Bot()
        without_token = core_models.ParserUser.objects.filter(subscribed = True, seller_api_token__isnull = True)

        for user_batch in [without_token[x:x + self.settings.API_MESSAGES_PER_SECOND_LIMIT]
                           for x in range(0, len(without_token), self.settings.API_MESSAGES_PER_SECOND_LIMIT)]:
            for user in user_batch:
                if bot.check_pc(user):
                    seller_api_token_filter(lambda *lambda_args: None)(None, bot, user, None)
            time.sleep(1)
