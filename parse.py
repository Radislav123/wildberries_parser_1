import copy
import sys

import pytest

from core import settings as core_settings
from parser_position import settings as parser_position_settings
from parser_price import settings as parser_price_settings
from parser_seller_api import settings as parser_seller_api_setting


class UnknownParserOption(Exception):
    pass


# todo: update README.md
class Runner:
    settings = core_settings.Settings()

    def run(self) -> None:
        """Разбирает поступающую из командной строки команду и выполняет заданные операции."""

        command = sys.argv[1]
        if command == self.settings.COMMAND_POSITION:
            self.settings = parser_position_settings.Settings()
        elif command == self.settings.COMMAND_PRICE:
            self.settings = parser_price_settings.Settings()
        elif command == self.settings.COMMAND_SELLER_API:
            raise ValueError("This parser is deprecated as standalone.")
            # self.settings = parser_seller_api_setting.Settings()
        else:
            raise UnknownParserOption(command)

        # опции командной строки, которые будут переданы в pytest
        pytest_options = sys.argv[2:]
        self.before_pytest()
        self.pytest(pytest_options)
        self.after_pytest()

    def before_pytest(self) -> None:
        pass

    def after_pytest(self) -> None:
        pass

    def pytest(self, args) -> None:
        pytest_args = copy.deepcopy(self.settings.PYTEST_ARGS)
        pytest_args.extend(args)
        pytest.main(pytest_args)


if __name__ == "__main__":
    Runner().run()
