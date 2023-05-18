import argparse
import copy
import sys

import pytest
from django.contrib.auth import get_user_model

# noinspection PyUnresolvedReferences
import configure_django
from logger import Logger
from parser_project import project_settings


class Runner:
    # оригинал - https://git.miem.hse.ru/447/framework/-/blob/master/service/run.py
    def __init__(self):
        self.options_parser = argparse.ArgumentParser()
        self.logger = Logger(self.__class__.__name__)

    def run(self):
        """Разбирает поступающую из командной строки команду и выполняет заданные операции."""

        # опции командной строки, которые будут переданы в pytest
        pytest_options = sys.argv[1:]
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
        pytest_args = copy.deepcopy(project_settings.PYTEST_ARGS)
        pytest_args.extend(args)
        pytest.main(pytest_args)


if __name__ == "__main__":
    Runner().run()
