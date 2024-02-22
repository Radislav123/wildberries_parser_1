from parser_price.management.commands import parser_price_command
from ... import models


class Command(parser_price_command.ParserPriceCommand):
    help = "Открывает окно авторизации Wildberries для парсера цен"

    def handle(self, *args, **options):
        models.Category.update_personal_discounts()
