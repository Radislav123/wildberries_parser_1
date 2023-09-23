import abc

from django.core.management.base import BaseCommand

import logger
from ... import settings


class CoreCommand(BaseCommand, abc.ABC):
    settings = settings.Settings()

    def __init__(self):
        super().__init__()
        self.logger = logger.Logger(self.__class__.__name__, None)
