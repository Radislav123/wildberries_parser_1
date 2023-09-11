import json
import logging
import os

from secret_keeper import SecretKeeper
from .apps import CoreConfig


# todo: move it to parsing_helper
class Settings:
    APP_NAME = CoreConfig.name

    def __init__(self):
        # Настройки selenium
        self.DEFAULT_TIMEOUT = 5

        # Данные для парсинга
        self.COMMAND_PRICE = "prices"
        self.COMMAND_POSITION = "positions"

        self.PARSING_DATA_FOLDER = "parsing_data"

        self.CITIES_PATH = f"{self.PARSING_DATA_FOLDER}/cities.json"
        self.CITIES = self.read_json(self.CITIES_PATH)
        self.MOSCOW_CITY_DICT = [x for x in self.CITIES if x["label"].lower() == "moscow"][0]

        self.PARSER_PRICE_DATA_PATH = f"{self.PARSING_DATA_FOLDER}/parser_price.xlsx"
        self.PARSER_POSITION_DATA_PATH = f"{self.PARSING_DATA_FOLDER}/parser_position.xlsx"

        self.WILDBERRIES_LOG_IN_DRIVER_DATA_PATH = f"{self.PARSING_DATA_FOLDER}/wildberries_log_in_driver_data.json"

        # Настройки административной панели
        # noinspection SpellCheckingInspection
        self.DOWNLOAD_EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        # количество дней, отображаемых в сводных таблицах
        self.SHOW_HISTORY_DEPTH = 14
        # количество дней, отображаемых в скачиваемых/выгружаемых excel-файлах
        self.DOWNLOAD_HISTORY_DEPTH = 30
        self.MAX_HISTORY_DEPTH = max(self.SHOW_HISTORY_DEPTH, self.DOWNLOAD_HISTORY_DEPTH)
        # если True - используются SHOW_HISTORY_DEPTH и DOWNLOAD_HISTORY_DEPTH,
        # иначе - отображаются и выгружаются все доступные даты
        # должно задаваться в дочерних классах
        self.DYNAMIC_FIELDS_ORDER: list[str] = []

        # Пути секретов
        self.SECRETS_FOLDER = "secrets"

        self.DATABASE_SECRETS_FOLDER = f"{self.SECRETS_FOLDER}/database"
        self.DATABASE_CREDENTIALS_PATH = f"{self.DATABASE_SECRETS_FOLDER}/credentials.json"

        self.ADMIN_PANEL_FOLDER = f"{self.SECRETS_FOLDER}/admin_panel"
        self.CUSTOMER_USER_CREDENTIALS_PATH = f"{self.ADMIN_PANEL_FOLDER}/customer_user.json"
        self.DEVELOPER_USER_CREDENTIALS_PATH = f"{self.ADMIN_PANEL_FOLDER}/developer_user.json"

        self.GEOPARSER_SECRETS_FOLDER = f"{self.SECRETS_FOLDER}/geoparser"
        self.GEOPARSER_CREDENTIALS_PATH = f"{self.GEOPARSER_SECRETS_FOLDER}/credentials.json"

        self.BOT_TELEGRAM_SECRETS_FOLDER = f"{self.SECRETS_FOLDER}/bot_telegram"
        self.BOT_TELEGRAM_CREDENTIALS_PATH = f"{self.BOT_TELEGRAM_SECRETS_FOLDER}/credentials.json"

        self.DEVELOPER_FOLDER = f"{self.SECRETS_FOLDER}/developer"
        self.DEVELOPER_CREDENTIALS_PATH = f"{self.DEVELOPER_FOLDER}/credentials.json"

        # Настройки логгера
        self.LOG_FORMAT = "[%(asctime)s] - [%(levelname)s] - %(name)s -" \
                          " (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
        self.LOG_FOLDER = "logs"
        self.CONSOLE_LOG_LEVEL = logging.DEBUG
        self.FILE_LOG_LEVEL = logging.DEBUG

        # Настройки pytest
        if "PYTEST_XDIST_WORKER_COUNT" in os.environ:
            self.PYTEST_XDIST_WORKER_COUNT = int(os.environ["PYTEST_XDIST_WORKER_COUNT"])
        else:
            self.PYTEST_XDIST_WORKER_COUNT = 1

        self.PYTEST_ARGS = [
            # путь до тестов
            "-o", f"testpaths={self.APP_NAME}",

            # игнорирование базовых тестов (родителей для наследования)
            "--ignore-glob=**/*base*",

            # соглашение об именовании тестов
            "-o", "python_files=parser.py",
            "-o", "python_classes=Parser*",
            # задается в parse.py
            # "-o", "python_functions=run",

            # вывод логов в командную строку
            "-o", "log_cli=true",
            "-o", f"log_cli_format={self.LOG_FORMAT}",

            # запрещает использование маркеров, если они не зарегистрированы
            # маркеры регистрируются в conftest.pytest_configure
            "--strict-markers",

            # https://docs.pytest.org/en/6.2.x/usage.html#detailed-summary-report
            "-rA",

            # указывает pytest, где находится файл настроек django
            # https://pytest-django.readthedocs.io/en/latest/tutorial.html#step-2-point-pytest-to-your-django-settings
            "-o", "DJANGO_SETTINGS_MODULE=parser_project.settings",

            # не используется, так как есть фикстура db_no_rollback
            # запрещает создание и удаление БД, вместо этого использует существующую
            # https://pytest-django.readthedocs.io/en/latest/database.html#reuse-db-reuse-the-testing-database-between-test-runs
            # "--reuse-db",

            # убирает экранирование не ASCII символов
            "-o", "disable_test_id_escaping_and_forfeit_all_rights_to_community_support=True",

            # разрешает пользовательский ввод в командной строке
            # не должно работать с pytest-xdist
            "-s",

            # pytest-xdist - запуск парсинга параллельно
            "--numprocesses=auto",
        ]

        # {marker_name: description}
        self.PYTEST_MARKERS = {}

        self.secrets = SecretKeeper(self)

    @staticmethod
    def read_json(path: str) -> list[dict[str, str | list[str]]]:
        with open(path, 'r', encoding = "utf-8") as file:
            data = json.load(file)
        return data

    # noinspection PyPep8Naming
    @property
    def APP_ROOT_PATH(self) -> str:
        return os.path.abspath(f"{__file__}/../../{self.APP_NAME}")
