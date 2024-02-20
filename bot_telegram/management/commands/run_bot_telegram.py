from bot_telegram.management.commands import telegram_bot_command
from ...bot import Bot


class Command(telegram_bot_command.TelegramBotCommand):
    help = "Запускает бота"

    def handle(self, *args, **options):
        bot = Bot()
        bot.start_polling()
