import argparse
import random

from core import models as core_models
from parser_price import models as parser_price_models
from bot_telegram.management.commands import telegram_bot_command
from ...bot import Bot


class Command(telegram_bot_command.TelegramBotCommand):
    help = "Отправляет тестовое оповещение"

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument("--developer", action = argparse.BooleanOptionalAction)
        parser.add_argument("--customer", action = argparse.BooleanOptionalAction)

    @staticmethod
    def construct_price(user: core_models.ParserUser) -> parser_price_models.Price:
        item = parser_price_models.Item.objects.filter(user = user).first()
        parsing = core_models.Parsing.objects.first()
        price = parser_price_models.Price(
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
            parser_price_models.Notification(
                new = self.construct_price(user),
                old = self.construct_price(user)
            )
        ]
        bot = Bot()
        try:
            bot.notify(notifications)
        except ValueError as error:
            if "save() prohibited to prevent data loss" in error.args[0] and error.__context__ is None:
                pass
            else:
                raise error.__context__
