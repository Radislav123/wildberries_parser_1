import time

import requests
from requests import JSONDecodeError

from core.settings import Settings
from logger import Logger


settings = Settings()
logger = Logger(f"{settings.APP_NAME}_service")


def parse_prices(
        vendor_codes: list[int],
        dest: str,
        regions: str
) -> tuple[dict[int, dict[str, int | float | str]], dict[int, Exception]]:
    # если указать СПП меньше реальной, придут неверные данные, при СПП >= 100 данные не приходят
    request_personal_sale = 99
    chunk_size = 100
    chunks = [vendor_codes[x: x + chunk_size] for x in range(0, len(vendor_codes), chunk_size)]
    prices = {}
    errors = {}

    for vendor_codes_chunk in chunks:
        # todo: сделать запросы асинхронными (ThreadPoolExecutor)
        url = (f"https://card.wb.ru/cards/detail?appType=1&curr=rub"
               f"&dest={dest}&regions={regions}&spp={request_personal_sale}"
               f"&nm={';'.join(str(x) for x in vendor_codes_chunk)}")
        items_response = requests.get(url)

        item_dicts = {x["id"]: x for x in items_response.json()["data"]["products"]}
        for vendor_code in vendor_codes_chunk:
            try:
                item_dict: dict = item_dicts[vendor_code]
                price, final_price, personal_sale, sold_out = get_price(item_dict)
                reviews_amount = int(item_dict["feedbacks"])
                category_name = get_category_name(vendor_code)
                name_site = f"{item_dict['brand']} / {item_dict['name']}"

                prices[vendor_code] = {
                    "price": price,
                    "final_price": final_price,
                    "personal_sale": personal_sale,
                    # todo: add sold_out to model
                    "sold_out": sold_out,
                    "reviews_amount": reviews_amount,
                    "category_name": category_name,
                    "name_site": name_site
                }
            except Exception as error:
                errors[vendor_code] = error

    return prices, errors


def get_price(item_dict: dict) -> tuple[float, float, int, bool]:
    sold_out = "wh" not in item_dict
    if sold_out:
        price = None
        final_price = None
        personal_sale = None
    else:
        if "basicPriceU" in item_dict["extended"]:
            price = item_dict["extended"]["basicPriceU"]
        else:
            price = item_dict["priceU"]
        final_price = item_dict["salePriceU"]
        if price == final_price:
            personal_sale = None
        else:
            personal_sale = int(item_dict["extended"]["clientSale"])
        price = int(price) / 100
        final_price = int(final_price) / 100
    return price, final_price, personal_sale, sold_out


def get_category_name(vendor_code: int) -> str:
    part = vendor_code // 1000
    vol = part // 100
    for basket in range(1, 99):
        # todo: сделать запросы асинхронными (ThreadPoolExecutor)
        category_url = (f"https://basket-{str(basket).rjust(2, '0')}.wb.ru/vol{vol}"
                        f"/part{part}/{vendor_code}/info/ru/card.json")
        category_response = requests.get(category_url)
        if category_response.status_code == 200:
            category_name = category_response.json()["subj_name"]
            break
    else:
        category_name = ""
    return category_name


# не использовать на прямую, так как нет проверки на наличие товара
def parse_position(vendor_code: int, keyword: str, dest: str, regions: str) -> dict[str, int | list[int]]:
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
            url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&curr=rub" \
                  f"&dest={dest}&page={page}&query={keyword}&regions={regions}" \
                  f"&resultset=catalog&sort=popular&spp=0&suppressSpellcheck=false"
            response = requests.get(url)
            try_number = 0
            try_success = False
            while try_number < settings.REQUEST_PAGE_ITEMS_ATTEMPTS_AMOUNT and not try_success:
                try_number += 1
                try:
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
    return {
        "page_capacities": page_capacities,
        "page": page,
        "position": position,
        "promo_page": promo_page,
        "promo_position": promo_position
    }


def parse_positions(
        vendor_codes: list[int],
        keywords: list[str],
        dest: str,
        regions: str
) -> tuple[dict[tuple[int, str], dict[str, int | list[int] | bool | None]], dict[int, Exception]]:
    prices, _ = parse_prices(list(set(vendor_codes)), dest, regions)

    positions = {}
    errors = {}
    for keyword, vendor_code in zip(keywords, vendor_codes):
        try:
            if prices[vendor_code]["sold_out"]:
                position = {
                    "page_capacities": None,
                    "page": None,
                    "position": None,
                    "promo_page": None,
                    "promo_position": None
                }
            else:
                position = parse_position(vendor_code, keyword, dest, regions)
            position["sold_out"] = prices[vendor_code]["sold_out"]
            positions[(vendor_code, keyword)] = position
        except Exception as error:
            errors[vendor_code] = error
    return positions, errors
