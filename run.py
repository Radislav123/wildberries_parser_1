import copy
import sys

import pytest

# noinspection PyUnresolvedReferences
import configure_django
from parser.settings import Settings


class UnknownParserOption(Exception):
    pass


class Runner:
    settings = Settings()

    def run(self):
        """Разбирает поступающую из командной строки команду и выполняет заданные операции."""

        command = sys.argv[1]
        if command == "positions":
            method_name = self.settings.POSITION_PARSER_METHOD_NAME
        elif command == "prices":
            method_name = self.settings.PRICE_PARSER_METHOD_NAME
        else:
            raise UnknownParserOption()
        pytest_options = [
            "-o", f"python_functions={method_name}",
            f"--parser={self.settings.PARSER_NAMES[method_name]}"
        ]

        # опции командной строки, которые будут переданы в pytest
        pytest_options.extend(sys.argv[2:])
        self.before_pytest()
        self.pytest(pytest_options)
        self.after_pytest()

    def before_pytest(self):
        pass

    def after_pytest(self):
        pass

    def pytest(self, args):
        pytest_args = copy.deepcopy(self.settings.PYTEST_ARGS)
        pytest_args.extend(args)
        pytest.main(pytest_args)


if __name__ == "__main__":
    Runner().run()
