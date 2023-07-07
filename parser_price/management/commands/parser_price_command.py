import abc

from core.management.commands import core_command
from ... import settings


class ParserPriceCommand(core_command.CoreCommand, abc.ABC):
    settings = settings.Settings()
