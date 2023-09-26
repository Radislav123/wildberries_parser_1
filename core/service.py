import requests


def parse_prices(
        vendor_codes: list[int],
        dest: str,
        regions: str
) -> tuple[dict[int, dict[str, int | float | str]], dict[int, Exception]]:
    # если указать СПП меньше реальной, придут неверные данные, при СПП >= 100 данные не приходят
    request_personal_sale = 99
    url = (f"https://card.wb.ru/cards/detail?appType=1&curr=rub"
           f"&dest={dest}&regions={regions}&spp={request_personal_sale}"
           f"&nm={';'.join([str(x) for x in vendor_codes])}")
    items_response = requests.get(url)

    item_dicts = {x["id"]: x for x in items_response.json()["data"]["products"]}
    prices = {}
    errors = {}
    for vendor_code in vendor_codes:
        try:
            item_dict: dict = item_dicts[vendor_code]
            price, final_price, personal_sale = get_price(item_dict)
            reviews_amount = int(item_dict["feedbacks"])
            category_name = get_category_name(vendor_code)
            name_site = f"{item_dict['brand']} / {item_dict['name']}"

            prices[vendor_code] = {
                "price": price,
                "final_price": final_price,
                "personal_sale": personal_sale,
                "reviews_amount": reviews_amount,
                "category_name": category_name,
                "name_site": name_site
            }
        except Exception as error:
            errors[vendor_code] = error

    return prices, errors


def get_price(item_dict: dict) -> tuple[float, float, int]:
    if "basicPriceU" not in item_dict["extended"]:
        # товар распродан
        price = None
        final_price = None
        personal_sale = None
    else:
        price = item_dict["extended"]["basicPriceU"]
        final_price = item_dict["salePriceU"]
        if price == final_price:
            personal_sale = None
        else:
            personal_sale = int(item_dict["extended"]["clientSale"])
        price = int(price) / 100
        final_price = int(final_price) / 100
    return price, final_price, personal_sale


def get_category_name(vendor_code: int) -> str:
    part = vendor_code // 1000
    vol = part // 100
    for basket in range(1, 99):
        category_url = (f"https://basket-{str(basket).rjust(2, '0')}.wb.ru/vol{vol}"
                        f"/part{part}/{vendor_code}/info/ru/card.json")
        category_response = requests.get(category_url)
        if category_response.status_code == 200:
            category_name = category_response.json()["subj_name"]
            break
    else:
        category_name = ""
    return category_name
