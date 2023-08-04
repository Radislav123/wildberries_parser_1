import json

import requests

# noinspection PyUnresolvedReferences
import configure_django
from parser_position.settings import Settings
from parser_price import models as parser_price_models
from bot_telegram.bot import Bot




def main():
    for item in parser_price_models.Item.objects.all():
        temp_item = parser_price_models


if __name__ == "__main__":
    main()
