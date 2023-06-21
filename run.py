import copy
import sys

import pytest
from django.contrib.auth import get_user_model

# noinspection PyUnresolvedReferences
import configure_django
from parser import settings


class UnknownParserOption(Exception):
    pass


class Runner:
    # оригинал - https://git.miem.hse.ru/447/framework/-/blob/master/service/run.py
    def run(self):
        """Разбирает поступающую из командной строки команду и выполняет заданные операции."""

        command = sys.argv[1]
        if command == "positions":
            settings.PARSE_POSITIONS = True
            method_name = settings.POSITION_PARSER_METHOD_NAME
        elif command == "prices":
            settings.PARSE_PRICES = True
            method_name = settings.PRICE_PARSER_METHOD_NAME
        else:
            raise UnknownParserOption()
        pytest_options = [
            "-o", f"python_functions={method_name}",
            f"--parser={settings.PARSER_NAMES[method_name]}"
        ]

        # опции командной строки, которые будут переданы в pytest
        pytest_options.extend(sys.argv[2:])
        self.before_pytest()
        self.pytest(pytest_options)
        self.after_pytest()

    @staticmethod
    def before_pytest():
        user = get_user_model()
        if not user.objects.filter(username = "admin").exists():
            user.objects.create_superuser("admin", "", "admin")

    def after_pytest(self):
        pass

    @staticmethod
    def pytest(args):
        pytest_args = copy.deepcopy(settings.PYTEST_ARGS)
        pytest_args.extend(args)
        pytest.main(pytest_args)


if __name__ == "__main__":
    Runner().run()
