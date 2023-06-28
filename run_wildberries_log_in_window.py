import json
import time

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import LogInPage
from parser.settings import Settings


def get_authorization_driver():
    options = ChromeOptions()

    options.add_argument("--no-sandbox")
    driver_manager = ChromeDriverManager(path = "").install()
    service = Service(executable_path = driver_manager)

    driver = Chrome(options = options, service = service)
    driver.maximize_window()
    return driver


def write_driver_info(driver: Chrome, settings: Settings) -> None:
    with open(settings.WILDBERRIES_LOG_IN_DRIVER_DATA_PATH, 'w') as file:
        # noinspection PyProtectedMember
        json.dump({"url": driver.command_executor._url, "session_id": driver.session_id}, file, indent = 2)


def main():
    settings = Settings()
    driver = get_authorization_driver()
    login_page = LogInPage(driver, settings)
    login_page.open()
    write_driver_info(driver, settings)
    while True:
        time.sleep(100)


if __name__ == "__main__":
    main()
