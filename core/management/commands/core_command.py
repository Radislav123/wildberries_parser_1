import abc

from django.core.management.base import BaseCommand

from ... import settings


# todo: поменять пароль
class CoreCommand(BaseCommand, abc.ABC):
    settings = settings.Settings()
