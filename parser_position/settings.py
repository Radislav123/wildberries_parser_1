from core import settings

from .apps import ParserPositionConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    NAME = ParserPositionConfig.name

    def __init__(self):
        super().__init__()
