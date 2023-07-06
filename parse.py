import copy
import sys

import pytest

from core import settings as core_settings
from parser_position import settings as parser_position_settings
from parser_price import settings as parser_price_settings


class UnknownParserOption(Exception):
    pass


# todo: update README.md
class Runner:
    settings = core_settings.Settings()

    def run(self):
        """Разбирает поступающую из командной строки команду и выполняет заданные операции."""

        command = sys.argv[1]
        if command == self.settings.COMMAND_POSITION:
            self.settings = parser_position_settings.Settings()
        elif command == self.settings.COMMAND_PRICE:
            self.settings = parser_price_settings.Settings()
        else:
            raise UnknownParserOption()

        # опции командной строки, которые будут переданы в pytest
        pytest_options = sys.argv[2:]
        self.before_pytest()
        self.pytest(pytest_options)
        self.after_pytest(command)

    def before_pytest(self):
        pass

    def after_pytest(self, command):
        pass

    def pytest(self, args):
        pytest_args = copy.deepcopy(self.settings.PYTEST_ARGS)
        pytest_args.extend(args)
        pytest.main(pytest_args)


if __name__ == "__main__":
    Runner().run()
