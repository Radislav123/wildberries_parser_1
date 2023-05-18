import time

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from web_elements import ExtendedWebElement
from .wildberries_base_page import WildberriesPage


# page_url = https://www.wildberries.ru/
class MainPage(WildberriesPage):
    class Map(ExtendedWebElement):
        def __init__(self, page: "MainPage", xpath: str) -> None:
            super().__init__(page, xpath)
            self.address_input = ExtendedWebElement(self.page, '//input[@placeholder = "Введите адрес"]')
            self.find_button = ExtendedWebElement(self.page, '//ymaps[@class = "ymaps-2-1-79-searchbox__button-cell"]')

    def __init__(self, driver: Chrome) -> None:
        super().__init__(driver)
        self.geo_link = ExtendedWebElement(self, '//span[contains(@class, "geocity-link")]')
        self.main_banner_container = ExtendedWebElement(
            self,
            '//div[contains(@class, "swiper-container j-main-banners")]'
        )

        self.map = self.Map(self, '//div[contains(@class, "geocity-pop")]')

    def set_city(self, city: str):
        # по рекламе определяется, когда страница загружена
        self.main_banner_container.init()
        self.geo_link.click()
        self.map.address_input.send_keys(city)
        self.map.address_input.send_keys(Keys.ENTER)

        # если есть выпадающий список с уточнением места
        time.sleep(3)
        clarifications = self.driver.find_elements(
            By.XPATH, '//ymaps[@class = "ymaps-2-1-79-islets_serp-item ymaps-2-1-79-islets__first"]'
        )
        if len(clarifications) > 0:
            clarifications[0].click()

        self.map.find_button.click()

        first_address_accepted = ExtendedWebElement(
            self,
            f'//div[contains(@class, "address-item")]/div/span/span[contains(text(), "{city}")]'
        )
        first_address_accepted.click()
        choose_button = ExtendedWebElement(self, '//button[@class = "details-self__btn btn-main"]')
        choose_button.click()
