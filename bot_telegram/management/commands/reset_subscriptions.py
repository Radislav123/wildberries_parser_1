from core import models as core_models
from parser_price.management.commands import parser_price_command


class Command(parser_price_command.ParserPriceCommand):
    help = "Сбрасывает подписка пользователей"

    def handle(self, *args, **options) -> None:
        users = core_models.ParserUser.objects.all()
        for user in users:
            user.subscribed = False

        core_models.ParserUser.objects.bulk_update(users, ("subscribed",))
