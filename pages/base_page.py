from selenium.webdriver import Chrome


class BasePage:
    def __init__(self, driver: Chrome, url: str):
        self.driver = driver
        self.url = url

    def open(self):
        self.driver.get(self.url)
