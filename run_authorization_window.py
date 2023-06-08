import json
import time

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pages import LogInPage
from parser import settings


def get_authorization_driver():
    options = ChromeOptions()

    driver_manager = ChromeDriverManager(path = "").install()
    service = Service(executable_path = driver_manager)

    driver = Chrome(options = options, service = service)
    driver.maximize_window()
    return driver


def write_driver_info(driver: Chrome) -> None:
    with open(settings.LOG_IN_DRIVER_DATA_PATH, 'w') as file:
        # noinspection PyProtectedMember
        json.dump({"url": driver.command_executor._url, "session_id": driver.session_id}, file, indent = 2)


def main():
    driver = get_authorization_driver()
    login_page = LogInPage(driver)
    login_page.open()
    write_driver_info(driver)
    while True:
        time.sleep(100)


if __name__ == "__main__":
    main()
