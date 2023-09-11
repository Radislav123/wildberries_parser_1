def get_price(item_dict: dict) -> tuple[float, float, int]:
    if "basicPriceU" not in item_dict["extended"]:
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
