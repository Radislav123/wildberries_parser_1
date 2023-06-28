import pytest
from _pytest.config import Config
from _pytest.python import FunctionDefinition, Metafunc

from parser.settings import Settings


settings = Settings()


@pytest.fixture(autouse = True)
def db_no_rollback(request, django_db_blocker):
    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.restore)


def pytest_addoption(parser):
    parser.addoption("--parser", choices = settings.PARSER_METHODS.keys())


# https://docs.pytest.org/en/7.1.x/reference/reference.html#pytest.hookspec.pytest_configure
def pytest_configure(config: Config):
    for marker in settings.PYTEST_MARKERS:
        config.addinivalue_line("markers", f"{marker}: {settings.PYTEST_MARKERS[marker]}")


def pytest_generate_tests(metafunc: Metafunc):
    # noinspection PyTypeHints
    metafunc.function: FunctionDefinition
    if metafunc.function.__name__ == "run_position_parsing":
        metafunc.parametrize(
            "city_dict",
            [pytest.param(city_dict, marks = pytest.mark.xdist_group(city_dict["name"]), id = city_dict["label"])
             for city_dict in settings.CITIES]
        )
