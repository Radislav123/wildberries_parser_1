from core import models as core_models
from parser_price.management.commands import parser_price_command
from ... import models


class Command(parser_price_command.ParserPriceCommand):
    help = "Открывает окно авторизации Wildberries для парсера цен"

    def handle(self, *args, **options):
        counter = 0
        for user in core_models.ParserUser.objects.exclude(id = core_models.ParserUser.get_customer().id):
            for item in models.Item.objects.filter(user = user):
                instances_to_delete = models.Price.objects.filter(item = item) \
                                          .order_by("-id")[self.settings.USER_HISTORY_DEPTH:]
                counter += len(instances_to_delete)
                models.Price.objects.filter(id__in = [x.id for x in instances_to_delete]).delete()
        self.logger.info(f"Удалено цен: {counter}")
