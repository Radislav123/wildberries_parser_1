import math
import os

import pytest
from _pytest.python import FunctionDefinition, Metafunc

from . import parser
from .settings import Settings


settings = Settings()


def pytest_generate_tests(metafunc: Metafunc):
    # noinspection PyTypeHints
    metafunc.function: FunctionDefinition
    all_vendor_codes = [x["vendor_code"] for x in parser.Parser.get_price_parser_item_dicts()]
    chunk_size = math.ceil(len(all_vendor_codes) / int(os.environ["PYTEST_XDIST_WORKER_COUNT"]))
    vendor_code_chunks = [all_vendor_codes[x:x + chunk_size] for x in range(0, len(all_vendor_codes), chunk_size)]
    metafunc.parametrize(
        "vendor_codes",
        [pytest.param(item_chunk, marks = pytest.mark.xdist_group(item_chunk)) for item_chunk in vendor_code_chunks]
    )
