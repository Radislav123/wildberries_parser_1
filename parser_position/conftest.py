import pytest
from _pytest.python import FunctionDefinition, Metafunc

from .settings import Settings


settings = Settings()

# todo: вернуть различные города?
# https://user-geo-data.wildberries.ru/get-geo-info?latitude=60.753737&longitude=37.6201&address=%D0%9C%D0%B0%D0%B3%D0%B0%D0%B4%D0%B0%D0%BD
# или сервис - https://geocodify-670.freshstatus.io/

def pytest_generate_tests(metafunc: Metafunc):
    # noinspection PyTypeHints
    metafunc.function: FunctionDefinition
    metafunc.parametrize(
        "city_dict",
        [pytest.param(city_dict, marks = pytest.mark.xdist_group(city_dict["name"]), id = city_dict["label"])
         # todo: оставить только Москву - временное решение
         for city_dict in settings.CITIES[:1]]
    )
