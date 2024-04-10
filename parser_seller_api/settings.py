from core import settings

from .apps import ParserSellerApiConfig


# todo: move it to parsing_helper
class Settings(settings.Settings):
    APP_NAME = ParserSellerApiConfig.name
    parallel = False

    def __init__(self) -> None:
        super().__init__()

        # убирается параллельный запуск
        for arg in self.PYTEST_ARGS.copy():
            if "numprocesses" in arg:
                self.PYTEST_ARGS.remove(arg)
                break
