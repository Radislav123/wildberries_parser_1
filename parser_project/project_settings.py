import logging


DEFAULT_TIMEOUT = 5

# Пути секретов
SECRETS_FOLDER = "secrets"

MAIL_SECRETS_FOLDER = f"{SECRETS_FOLDER}/mail"
MAIL_CREDENTIALS_PATH = f"{MAIL_SECRETS_FOLDER}/credentials.txt"

SMS_ACTIVATE_SECRETS_FOLDER = f"{SECRETS_FOLDER}/sms_activate"
SMS_ACTIVATE_CREDENTIALS_PATH = f"{SMS_ACTIVATE_SECRETS_FOLDER}/credentials.txt"
SMS_ACTIVATE_API_KEY_PATH = f"{SMS_ACTIVATE_SECRETS_FOLDER}/api_key.txt"

WILDBERRIES_SECRETS_FOLDER = f"{SECRETS_FOLDER}/wildberries"
WILDBERRIES_AUTH_COOKIE_PATH = f"{WILDBERRIES_SECRETS_FOLDER}/auth_cookie.txt"

# Настройки логгера
LOG_FORMAT = "[%(asctime)s] - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
LOG_FOLDER = "logs"
CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.DEBUG

# Настройки, связанные с sms-activate
# в днях
RENT_DURATION = 10
WILDBERRIES_SERVICE_CODE = "uu"
