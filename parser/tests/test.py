import time

from django.test import TestCase
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from smsactivate.api import SMSActivateAPI
from webdriver_manager.chrome import ChromeDriverManager

from pages import ItemPage, MainPage
from parser_project import project_settings


class SecretKeeper:
    class CredentialsOnly:
        def __init__(self, login: str, password: str) -> None:
            self.login = login
            self.password = password

        def __str__(self) -> str:
            return f"login: {self.login}\npassword: {self.password}"

    class Cookie:
        def __init__(self, name: str, value: str) -> None:
            self.name = name
            self.value = value

        def __str__(self) -> str:
            return f"name: {self.name}\nvalue: {self.value}"

        def to_dict(self) -> dict[str, str]:
            return {"name": self.name, "value": self.value}

    # todo: remove?
    class SMSActivate(CredentialsOnly):
        def __init__(self, login: str, password: str, api_key: str) -> None:
            super().__init__(login, password)
            self.api_key = api_key

        def __str__(self) -> str:
            return f"{super().__str__()}\napi_key: {self.api_key}"

    def __init__(self) -> None:
        self.mail = self.CredentialsOnly(*self.read_secret(project_settings.MAIL_CREDENTIALS_PATH))
        self.sms_activate = self.SMSActivate(
            *self.read_secret(project_settings.SMS_ACTIVATE_CREDENTIALS_PATH),
            *self.read_secret(project_settings.SMS_ACTIVATE_API_KEY_PATH)
        )
        self.wildberries_auth = self.Cookie(*self.read_secret(project_settings.WILDBERRIES_AUTH_COOKIE_PATH))

    @staticmethod
    def read_secret(path: str) -> list[str]:
        with open(path, 'r') as file:
            data = [x.strip() for x in file]
        return data


class Test(TestCase):
    """Отвечает за весь процесс парсинга."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        options = ChromeOptions()
        options.add_argument("--start-maximized")

        driver_manager = ChromeDriverManager(path = "").install()
        service = Service(executable_path = driver_manager)

        self.driver = Chrome(options = options, service = service)
        self.secrets = SecretKeeper()
        self.sms_api = SMSActivateAPI(self.secrets.sms_activate.api_key)

    def rent_number(self) -> dict[str, str]:
        return self.sms_api.getRentNumber(
            project_settings.WILDBERRIES_SERVICE_CODE,
            # todo: изменить на использование RENT_DURATION => RENT_DURATION * 24
            4
        )

    def test(self):
        main_page = MainPage(self.driver)
        main_page.authorize_and_open(self.secrets.wildberries_auth)
        time.sleep(3)

    def sms_api_123(self):
        rent_list = self.sms_api.getRentList()
        if rent_list["status"] == "error" and rent_list["message"] == "NO_NUMBERS":
            print(self.rent_number())
            rent_list = self.sms_api.getRentList()

        activation_id = rent_list["values"]["0"]["id"]
        print(activation_id)
        print(self.sms_api.getRentStatus(activation_id))

    def change_city_example(self):
        main_page = MainPage(self.driver)
        main_page.open()
        # todo: вынести выбор города в параметризацию
        main_page.set_city("Казань")
        time.sleep(5)

    def parse_old(self):
        item_page = ItemPage(self.driver)
        item_page.open()
        print(item_page.vendor_code.text)
