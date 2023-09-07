import pytest
from _pytest.python import FunctionDefinition, Metafunc

from .settings import Settings


settings = Settings()


def pytest_generate_tests(metafunc: Metafunc):
    # noinspection PyTypeHints
    metafunc.function: FunctionDefinition
    metafunc.parametrize(
        "city_dict",
        [pytest.param(city_dict, marks = pytest.mark.xdist_group(city_dict["name"]), id = city_dict["label"])
         # todo: оставить только Москву - временное решение
         for city_dict in settings.CITIES[:1]]
    )
