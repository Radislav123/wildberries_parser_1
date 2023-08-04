import random

from core import models as core_models
from parser_price import models
from parser_price.management.commands import parser_price_command
from ...bot import Bot


class Command(parser_price_command.ParserPriceCommand):
    help = "Отправляет тестовое оповещение"

    @staticmethod
    def construct_price() -> models.Price:
        item = models.Item.objects.filter(user = core_models.ParserUser.get_customer()).first()
        parsing = core_models.Parsing.objects.first()
        price = models.Price(
            item = item,
            parsing = parsing,
            reviews_amount = random.randint(0, 100),
            price = random.randint(0, 1000),
            personal_sale = random.randint(0, 100)
        )
        price.final_price = price.price * (100 - price.personal_sale) / 100
        return price

    def handle(self, *args, **options) -> None:
        notifications = [
            models.Price.Notification(
                self.construct_price(),
                self.construct_price(),
                False,
                False
            )
        ]
        bot = Bot()
        bot.notify(notifications)
