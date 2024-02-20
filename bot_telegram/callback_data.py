class CallbackData:
    DELIMITER = ":"
    ACTION = "a"

    SEND_TO_USERS = "00"

    # xx_yy
    # xx - идентификатор обратного вызова
    # yy - идентификатор команды обратного вызова
    SEND_TO_USERS_SEND = f"{SEND_TO_USERS}_00"
    SEND_TO_USERS_CANCEL = f"{SEND_TO_USERS}_01"

    # a_xx
    # a - action - действие
    # xx - идентификатор действия
    PARSE_ITEM = f"{ACTION}_00"
    ADD_ITEM = f"{ACTION}_01"
    REMOVE_ITEM = f"{ACTION}_02"
    GET_ALL_ITEMS = f"{ACTION}_03"
    UPDATE_SUBSCRIPTIONS = f"{ACTION}_04"
    CHECK_SUBSCRIPTIONS = f"{ACTION}_05"
    UPDATE_SELLER_API_TOKEN = f"{ACTION}_06"
    CHECK_SELLER_API_TOKEN = f"{ACTION}_07"
