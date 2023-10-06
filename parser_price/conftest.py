import pytest
from _pytest.python import Metafunc

from logger import Logger
from .settings import Settings


settings = Settings()
logger = Logger(f"{settings.APP_NAME}_conftest")


def pytest_generate_tests(metafunc: Metafunc):
    metafunc.parametrize(
        "division_remainder",
        [pytest.param(x, marks = pytest.mark.xdist_group(x)) for x in range(settings.PYTEST_XDIST_WORKER_COUNT)]
    )
