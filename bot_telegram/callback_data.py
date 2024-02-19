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
