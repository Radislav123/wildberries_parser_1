from parser_price.management.commands import parser_price_command
from ...bot import Bot


class Command(parser_price_command.ParserPriceCommand):
    help = "Запускает бота для возможности авторизоваться администратора"

    def handle(self, *args, **options):
        bot = Bot()
        bot.start_polling()
