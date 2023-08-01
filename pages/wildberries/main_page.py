import json
import time
from typing import TYPE_CHECKING

import requests
from parsing_helper.web_elements import ExtendedWebElement, ExtendedWebElementCollection
from requests.exceptions import JSONDecodeError
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import presence_of_all_elements_located

from .wildberries_base_page import WildberriesPage


if TYPE_CHECKING:
    from parser_position.parser import City


class NotFoundGeoError(Exception):
    pass


# page_url = https://www.wildberries.ru/
class MainPage(WildberriesPage):
    class Map(ExtendedWebElement):
        def __init__(self, page: "MainPage", xpath: str) -> None:
            super().__init__(page, xpath)
            self.address_input = ExtendedWebElement(self.page, '//input[@placeholder = "Введите адрес"]')
            self.find_button = ExtendedWebElement(self.page, '//ymaps[@class = "ymaps-2-1-79-searchbox__button-cell"]')

    def __init__(self, parser) -> None:
        super().__init__(parser)
        self.geo_link = ExtendedWebElement(self, '//span[contains(@class, "geocity-link")]')
        self.main_banner_container = ExtendedWebElement(
            self,
            '//div[contains(@class, "swiper-container j-main-banners")]'
        )

        self.map = self.Map(self, '//div[contains(@class, "geocity-pop")]')

    def get_ll(self, address: str, city_dict: "City") -> tuple[str | None, str | None]:
        # noinspection HttpUrlsUsage
        url = "http://api.positionstack.com/v1/forward"
        with open(self.settings.GEOPARSER_CREDENTIALS_PATH, 'r') as file:
            credentials = json.load(file)
        # noinspection SpellCheckingInspection
        params = {
            "access_key": credentials["api_key"],
            "query": address,
            "limit": 1
        }
        response = requests.get(url, params)

        try:
            data = response.json()["data"]
            if len(data) > 0:
                data = data[0]
                latitude = data["latitude"]
                longitude = data["longitude"]
            else:
                latitude = None
                longitude = None
        except (JSONDecodeError, TypeError):
            latitude = None
            longitude = None
        except KeyError as error:
            if "data" in error.args:
                latitude = city_dict["latitude"]
                longitude = city_dict["longitude"]
            else:
                raise error
        return latitude, longitude

    @staticmethod
    def get_geo(latitude: str, longitude: str, address: str) -> tuple[str, str]:
        url = f"https://user-geo-data.wildberries.ru/get-geo-info"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "address": address,
            "currency": "RUB",
            "locale": "ru"
        }
        response = requests.get(url, params)
        data = response.json()["xinfo"].split("&")
        dest = data[2].split("=")[-1]
        regions = data[3].split("=")[-1]
        return dest, regions

    def set_city(self, city_dict: "City") -> tuple[str, str]:
        # по рекламе определяется, когда страница загружена
        self.main_banner_container.init()
        self.geo_link.click()
        self.map.address_input.send_keys(city_dict["name"])
        self.map.address_input.send_keys(Keys.ENTER)

        # если есть выпадающий список с уточнением места
        time.sleep(3)
        clarifications = self.driver.find_elements(
            By.XPATH, '//ymaps[@class = "ymaps-2-1-79-islets_serp-item ymaps-2-1-79-islets__first"]'
        )
        if len(clarifications) > 0:
            clarifications[0].click()
        else:
            self.map.find_button.click()

        addresses_accepted = ExtendedWebElementCollection(
            self,
            f'//div[contains(@class, "address-item")]/div/span/span[contains(text(), "{city_dict["name"]}")]'
        )
        # при выборе пункта выдаче в некоторых городах (Краснодар) элементы списка пункта выдачи
        # вызывают ошибку StaleElementReferenceException без ожидания
        time.sleep(3)
        addresses_accepted = addresses_accepted.wait.until(
            presence_of_all_elements_located((By.XPATH, addresses_accepted.xpath))
        )
        for address in addresses_accepted:
            latitude, longitude = self.get_ll(address.text, city_dict)
            if latitude is not None and longitude is not None:
                address_accepted = address
                dest, regions = self.get_geo(latitude, longitude, address)
                break
        else:
            raise NotFoundGeoError()
        address_accepted.click()
        choose_button = ExtendedWebElement(self, '//button[@class = "details-self__btn btn-main"]')
        choose_button.click()
        return dest, regions
