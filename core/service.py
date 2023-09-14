import requests


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


def get_name_site(item_dict: dict) -> str:
    return f"{item_dict['brand']} / {item_dict['name']}"


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
