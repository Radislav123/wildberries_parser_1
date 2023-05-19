import json
import logging
import os


def read_file(path: str) -> list[str]:
    with open(path, 'r', encoding = "utf-8") as file:
        data = [x.strip() for x in file]
    return data


def read_json(path: str) -> list[dict[str, str | list[str]]]:
    with open(path, 'r', encoding = "utf-8") as file:
        data = json.load(file)
    return data


PROJECT_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

# Настройки selenium
DEFAULT_TIMEOUT = 5

# Данные для парсинга
PARSER_DATA_FOLDER = "parser_data"

CITIES_PATH = f"{PARSER_DATA_FOLDER}/cities.json"
CITIES = read_json(CITIES_PATH)

ITEMS_PATH = f"{PARSER_DATA_FOLDER}/items.json"
ITEMS = read_json(ITEMS_PATH)

# Настройки административной панели
# количество дней для расчета средней позиции
AVERAGE_POSITION_PERIOD = 30

# Пути секретов
SECRETS_FOLDER = "secrets"

WILDBERRIES_SECRETS_FOLDER = f"{SECRETS_FOLDER}/wildberries"
WILDBERRIES_AUTH_COOKIE_PATH = f"{WILDBERRIES_SECRETS_FOLDER}/auth_cookie.txt"

DATABASE_SECRETS_FOLDER = f"{SECRETS_FOLDER}/database"
DATABASE_SETTINGS_PATH = f"{DATABASE_SECRETS_FOLDER}/credentials.json"

# Настройки логгера
LOG_FORMAT = "[%(asctime)s] - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
LOG_FOLDER = "logs"
CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.DEBUG

# Настройки pytest
PYTEST_ARGS = [
    # путь до тестов
    "-o", f"testpaths={PROJECT_ROOT_PATH}/parser",

    # игнорирование базовых тестов (родителей для наследования)
    "--ignore-glob=**/*base*",

    # соглашение об именовании тестов
    "-o", "python_files=*.py",
    "-o", "python_classes=*Parser",
    "-o", "python_functions=run",

    # вывод логов в командную строку
    "-o", "log_cli=true",
    "-o", f"log_cli_format={LOG_FORMAT}",

    # запрещает использование маркеров, если они не зарегистрированы
    # маркеры регистрируются в conftest.pytest_configure
    "--strict-markers",

    # https://docs.pytest.org/en/6.2.x/usage.html#detailed-summary-report
    "-rA",

    # указывает pytest, где находится файл настроек django
    # https://pytest-django.readthedocs.io/en/latest/tutorial.html#step-2-point-pytest-to-your-django-settings
    "-o", "DJANGO_SETTINGS_MODULE=parser_project.settings",

    # запрещает создание и удаление БД, вместо этого использует существующую
    # https://pytest-django.readthedocs.io/en/latest/database.html#reuse-db-reuse-the-testing-database-between-test-runs
    "--reuse-db",

    # убирает экранирование не ASCII символов
    "-o", "disable_test_id_escaping_and_forfeit_all_rights_to_community_support=True",
]
