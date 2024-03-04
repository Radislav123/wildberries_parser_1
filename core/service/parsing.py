import dataclasses
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import requests
from requests import JSONDecodeError

from core.settings import Settings
from logger import Logger
from parser_price import models as price_models
from parser_seller_api import models as seller_api_models


settings = Settings()
logger = Logger(f"{settings.APP_NAME}_service")

Path(settings.PARSING_RESOURCES_PATH).mkdir(parents = True, exist_ok = True)
BASKETS_PATH = f"{settings.PARSING_RESOURCES_PATH}/temp_basket_entities.json"


@dataclasses.dataclass
class ParsedPrice:
    price: int | None
    personal_discount: int | None
    final_price: int
    sold_out: bool
    reviews_amount: int
    category: price_models.Category | None
    name_site: str | None


@dataclasses.dataclass
class ParsedPosition:
    page_capacities: list[str] | None
    page: int | None
    position: int | None
    promo_page: int | None
    promo_position: int | None
    sold_out: int | None = None


def parse_prices(
        vendor_codes: list[int],
        dest: str,
        items_categories: dict[int, price_models.Category] = None,
        parse_categories = True
) -> tuple[dict[int, ParsedPrice], dict[int, Exception]]:
    # если указать СПП меньше реальной, придут неверные данные, при СПП >= 100 данные не приходят
    request_personal_discount = 99
    chunk_size = 100
    chunks = [vendor_codes[x: x + chunk_size] for x in range(0, len(vendor_codes), chunk_size)]
    prices = {}
    errors = {}
    seller_api_items: dict[int, seller_api_models.Item] = {x.vendor_code: x for x in
                                                           seller_api_models.Item.objects.all()}
    seller_api_items_by_category = defaultdict(list)
    for item in seller_api_items.values():
        seller_api_items_by_category[item.category].append(item)
    seller_api_items_by_category = {key: sorted(value, key = lambda x: x.real_price)
                                    for key, value in seller_api_items_by_category.items()}

    try:
        with open(BASKETS_PATH, 'r') as file:
            baskets = json.load(file)
            if baskets[0] == "":
                baskets = []
    except FileNotFoundError:
        baskets = []
    baskets_order = get_baskets_order(baskets)

    for vendor_codes_chunk in chunks:
        # todo: сделать запросы асинхронными (ThreadPoolExecutor)
        url = (f"https://card.wb.ru/cards/detail?appType=1&curr=rub"
               f"&dest={dest}&spp={request_personal_discount}"
               f"&nm={';'.join(str(x) for x in vendor_codes_chunk)}")
        items_response = requests.get(url)

        item_dicts = {x["id"]: x for x in items_response.json()["data"]["products"]}
        for vendor_code in vendor_codes_chunk:
            try:
                item_dict: dict = item_dicts[vendor_code]
                final_price, sold_out = get_price(item_dict)
                reviews_amount = int(item_dict["feedbacks"])
                name_site = f"{item_dict['brand']} / {item_dict['name']}"

                if parse_categories:
                    if vendor_code in items_categories:
                        category = items_categories[vendor_code]
                    else:
                        category_name, basket = get_category_name(baskets_order, vendor_code)
                        baskets.append(basket)
                        category = price_models.Category.objects.get_or_create(name = category_name)[0]
                else:
                    category = None

                if vendor_code in seller_api_items:
                    seller_api_item = seller_api_items[vendor_code]
                    price = seller_api_item.real_price
                    personal_discount = round((1 - final_price / price) * 100)
                elif category in seller_api_items_by_category:
                    personal_discount, price = get_nearest_personal_discount(
                        seller_api_items_by_category[category],
                        final_price
                    )
                else:
                    price = None
                    personal_discount = None

                prices[vendor_code] = ParsedPrice(
                    price,
                    personal_discount,
                    final_price,
                    sold_out,
                    reviews_amount,
                    category,
                    name_site
                )
            except Exception as error:
                errors[vendor_code] = error

    entities_threshold = 10000
    if len(baskets) > entities_threshold:
        left = len(baskets) - entities_threshold
    else:
        left = 0
    with open(BASKETS_PATH, 'w') as file:
        json.dump(baskets[left:], file)

    return prices, errors


def get_nearest_personal_discount(
        items: list[seller_api_models.Item],
        final_price: int
) -> tuple[int | None, int | None]:
    if len(items) == 0:
        nearest_discount = None
        price = None
    else:
        differences = {abs(final_price - item.final_price): item for item in items
                       if item.final_price and item.personal_discount}
        if differences:
            nearest_item = differences[min(differences)]
            nearest_discount = nearest_item.personal_discount
            price = round(final_price / (100 - nearest_discount) * 100)
        else:
            nearest_discount = None
            price = None

    return nearest_discount, price


def get_price(item_dict: dict) -> tuple[int, bool]:
    sold_out = True
    for size in item_dict["sizes"]:
        if len(size["stocks"]) > 0:
            sold_out = False
            break
    final_price = round(int(item_dict["salePriceU"]) / 100)
    return final_price, sold_out


def get_baskets_order(baskets: Iterable[int]) -> tuple[int, ...]:
    basket_weights = Counter(map(int, baskets))
    for i in range(1, 50):
        if i not in basket_weights:
            basket_weights[i] = 0
    return tuple(key for key, value in sorted(basket_weights.items(), key = lambda item: -item[1]))


# todo: переписать это, чтобы basket получался, а не угадывался
def get_category_name(baskets_order: Iterable[int], vendor_code: int) -> tuple[str, int]:
    part = vendor_code // 1000
    vol = part // 100
    for basket in baskets_order:
        # todo: сделать запросы асинхронными (ThreadPoolExecutor)?
        category_url = (f"https://basket-{str(basket).rjust(2, '0')}.wb.ru/vol{vol}"
                        f"/part{part}/{vendor_code}/info/ru/card.json")
        category_response = requests.get(category_url)
        if category_response.status_code == 200:
            category_name = category_response.json()["subj_name"]
            break
    else:
        category_name = ""
    # noinspection PyUnboundLocalVariable
    return category_name, basket


# не использовать на прямую, так как нет проверки на наличие товара
def parse_position(vendor_code: int, keyword: str, dest: str) -> ParsedPosition:
    try:
        page = 1
        position = None
        promo_page = None
        promo_position = None
        page_capacities = []
        while page:
            # todo: сделать запросы асинхронными (ThreadPoolExecutor)
            # todo: можно ускорить, если искать по одному ключевому запросу сразу несколько товаров
            # noinspection SpellCheckingInspection
            url = (f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&curr=rub&dest={dest}&page={page}"
                   f"&query={keyword}&resultset=catalog&sort=popular&spp=0&suppressSpellcheck=false")
            try_number = 0
            try_success = False
            while try_number < settings.REQUEST_PAGE_ITEMS_ATTEMPTS_AMOUNT and not try_success:
                try_number += 1
                try:
                    response = requests.get(url)
                    response_json = response.json()
                    products = response_json["data"]["products"]
                    page_vendor_codes = [x["id"] for x in products]
                    logs = {x["id"]: x["log"] for x in products if "log" in x and len(x["log"])}
                    try_success = True
                except JSONDecodeError:
                    if not try_success and try_number >= settings.REQUEST_PAGE_ITEMS_ATTEMPTS_AMOUNT:
                        page = None
                        break
                    else:
                        # еще одна попытка
                        time.sleep(1)
            else:
                # noinspection PyUnboundLocalVariable
                page_capacities.append(len(page_vendor_codes))
                # noinspection PyUnboundLocalVariable
                if vendor_code in page_vendor_codes:
                    position = page_vendor_codes.index(vendor_code) + 1
                    # noinspection PyUnboundLocalVariable
                    if vendor_code in logs:
                        promo_page = page
                        promo_position = position
                        # предполагается, что емкость каждой страницы совпадает с емкостью первой
                        page = logs[vendor_code]["position"] // page_capacities[0] + 1
                        position = logs[vendor_code]["position"] % page_capacities[0] + 1
                    break
                elif "original" in response_json["metadata"]:
                    # страницы закончились, теперь идет другая выдача
                    page = None
                    break
                page += 1
    except KeyError as error:
        if "data" in error.args:
            # если возвращаемая позиция == None => товар не был найден по данному ключевому слову
            page_capacities = None
            page = None
            position = None
            promo_page = None
            promo_position = None
        else:
            raise error
    return ParsedPosition(page_capacities, page, position, promo_page, promo_position)


def parse_positions(
        vendor_codes: list[int],
        keywords: list[str],
        dest: str
) -> tuple[dict[tuple[int, str], ParsedPosition], dict[int, Exception]]:
    prices, _ = parse_prices(list(set(vendor_codes)), dest, parse_categories = False)

    positions = {}
    errors = {}
    for keyword, vendor_code in zip(keywords, vendor_codes):
        try:
            if prices[vendor_code].sold_out:
                position = ParsedPosition(None, None, None, None, None)
            else:
                position = parse_position(vendor_code, keyword, dest)
            position.sold_out = prices[vendor_code].sold_out
            positions[(vendor_code, keyword)] = position
        except Exception as error:
            errors[vendor_code] = error
    return positions, errors
