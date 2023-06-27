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


def prepare_settings(test_name: str):
    if test_name == "run_price_parsing":
        global PARSE_PRICES
        PARSE_PRICES = True
    elif test_name == "run_position_parsing":
        global PARSE_POSITIONS
        PARSE_POSITIONS = True


PROJECT_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

# Настройки selenium
DEFAULT_TIMEOUT = 5

# Настройки парсера
PRICE_PARSER_METHOD_NAME = "run_price_parsing"
POSITION_PARSER_METHOD_NAME = "run_position_parsing"
PARSER_METHODS = {"prices": PRICE_PARSER_METHOD_NAME, "positions": POSITION_PARSER_METHOD_NAME}
PARSER_NAMES = {PARSER_METHODS[x]: x for x in PARSER_METHODS}
PARSE_PRICES = False
PARSE_POSITIONS = False
ATTEMPTS_AMOUNT = 10
LOG_IN_ATTEMPTS_AMOUNT = 3

# Данные для парсинга
PARSER_DATA_FOLDER = "parser_data"

CITIES_PATH = f"{PARSER_DATA_FOLDER}/cities.json"
CITIES = read_json(CITIES_PATH)

PRICE_PARSER_DATA_PATH = f"{PARSER_DATA_FOLDER}/price_parser_data.xlsx"
POSITION_PARSER_DATA_PATH = f"{PARSER_DATA_FOLDER}/position_parser_data.xlsx"

LOG_IN_DRIVER_DATA_PATH = f"{PARSER_DATA_FOLDER}/log_in_driver_data.json"

# Настройки административной панели
# noinspection SpellCheckingInspection
DOWNLOAD_EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# количество дней, отображаемых в сводных таблицах
SHOW_HISTORY_DEPTH = 14
# количество дней, отображаемых в скачиваемых/выгружаемых excel-файлах
DOWNLOAD_HISTORY_DEPTH = 30
# если True - используются SHOW_HISTORY_DEPTH и DOWNLOAD_HISTORY_DEPTH,
# иначе - отображаются и выгружаются все доступные даты
USE_HISTORY_DEPTH = True
# количество дней для расчета долгих изменений позиции
LONG_MOVEMENT_DELTA = 5

# Пути секретов
SECRETS_FOLDER = "secrets"

DATABASE_SECRETS_FOLDER = f"{SECRETS_FOLDER}/database"
DATABASE_SETTINGS_PATH = f"{DATABASE_SECRETS_FOLDER}/credentials.json"

GEOPARSER_SECRETS_FOLDER = f"{SECRETS_FOLDER}/geoparser"
GEOPARSER_CREDENTIALS_PATH = f"{GEOPARSER_SECRETS_FOLDER}/credentials.json"

LOG_IN_SECRETS_FOLDER = f"{SECRETS_FOLDER}/log_in"
LOG_IN_CREDENTIALS_PATH = f"{LOG_IN_SECRETS_FOLDER}/credentials.json"

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
    # задается в run.Runner.run
    # "-o", "python_functions=run*",

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

    # разрешает пользовательский ввод в командной строке
    # не должно работать с pytest-xdist
    "-s",

    # pytest-xdist - запуск парсинга параллельно
    "--numprocesses=auto",
]

# {marker_name: description}
PYTEST_MARKERS = {}
