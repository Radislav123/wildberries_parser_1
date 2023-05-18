import pytest


@pytest.fixture(autouse = True)
def db_no_rollback(request, django_db_blocker):
    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.restore)
