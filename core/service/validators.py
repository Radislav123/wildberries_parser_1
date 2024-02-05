from core import models as core_models


def validate_seller_api_token(user: core_models.ParserUser) -> bool:
    return (user == core_models.ParserUser.get_customer() or user == core_models.ParserUser.get_developer()
            or user.seller_api_token)


def validate_subscriptions(user: core_models.ParserUser) -> bool:
    return (user == core_models.ParserUser.get_customer() or user == core_models.ParserUser.get_developer()
            or user.subscribed)
