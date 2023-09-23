import pytest
from _pytest.config import Config

from core.settings import Settings
from logger import Logger


settings = Settings()
logger = Logger(__name__, None)


@pytest.fixture(autouse = True)
def db_no_rollback(request, django_db_blocker):
    """Отменяет создание тестовой БД и очистку используемой БД после тестов."""

    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.restore)


# https://docs.pytest.org/en/7.1.x/reference/reference.html#pytest.hookspec.pytest_configure
def pytest_configure(config: Config):
    for marker in settings.PYTEST_MARKERS:
        config.addinivalue_line("markers", f"{marker}: {settings.PYTEST_MARKERS[marker]}")
