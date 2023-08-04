import json

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.settings import Settings


# todo: replace (inherit from) with one from parsing_helper
# todo: update one from parsing_helper with this one
class SecretKeeper:
    class Module:
        name: str
        secrets_path: str
        json: dict
        secret_keeper: "SecretKeeper"

        def get_dict(self) -> dict:
            return self.json

    class Database(Module):
        ENGINE: str
        NAME: str
        USER: str
        PASSWORD: str
        HOST: str
        PORT: str

    class CustomerUser(Module):
        username: str
        email: str
        password: str

    class Geoparser(Module):
        site: str
        login: str
        password: str
        api_key: str

    class BotTelegram(Module):
        token: str
        name: str
        username: str

    class WildberriesLogInDriver(Module):
        url: str
        session_id: str

    database: Database
    customer_user: CustomerUser
    geoparser: Geoparser
    bot_telegram: BotTelegram
    wildberries_log_in_driver: WildberriesLogInDriver

    def __init__(self, settings: "Settings") -> None:
        self.add_module("database", settings.DATABASE_CREDENTIALS_PATH)
        self.add_module("customer_user", settings.CUSTOMER_USER_CREDENTIALS_PATH)
        self.add_module("geoparser", settings.GEOPARSER_CREDENTIALS_PATH)
        self.add_module("bot_telegram", settings.BOT_TELEGRAM_CREDENTIALS_PATH)
        self.add_module("wildberries_log_in_driver", settings.WILDBERRIES_LOG_IN_DRIVER_DATA_PATH)

    @staticmethod
    def read_json(path: str) -> dict:
        with open(path, 'r') as file:
            data = json.load(file)
        return data

    def add_module(self, name: str, secrets_path: str) -> None:
        json_dict = self.read_json(secrets_path)
        module = type(name, (self.Module,), json_dict)()
        module.name = name
        module.secrets_path = secrets_path
        module.json = json_dict
        module.secret_keeper = self
        setattr(self, name, module)
