import argparse
import random

from core import models as core_models
from parser_price import models
from parser_price.management.commands import parser_price_command
from ...bot import Bot


class Command(parser_price_command.ParserPriceCommand):
    help = "Отправляет тестовое оповещение"

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument("--developer", action = argparse.BooleanOptionalAction)
        parser.add_argument("--customer", action = argparse.BooleanOptionalAction)

    @staticmethod
    def construct_price(user: core_models.ParserUser) -> models.Price:
        item = models.Item.objects.filter(user = user).first()
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
        if options["customer"]:
            user = core_models.ParserUser.get_customer()
        elif options["developer"]:
            user = core_models.ParserUser.get_developer()
        else:
            raise ValueError("Set --customer or --developer option")
        notifications = [
            models.Price.Notification(
                self.construct_price(user),
                self.construct_price(user),
                False,
                False
            )
        ]
        bot = Bot()
        bot.notify(notifications)
