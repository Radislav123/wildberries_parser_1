import openpyxl

from core import models as core_models, parser as parser_core
from core.service import parsing
from . import models, settings


City = dict[str, str]


class Parser(parser_core.Parser):
    settings = settings.Settings()
    parsing_type = core_models.Parsing.Type.POSITION

    def parse_positions(
            self,
            keywords: list[models.Keyword],
            dest: str,
            city: str
    ) -> tuple[list[models.Position], dict[models.Item, Exception]]:
        keywords_dict = {(x.item.vendor_code, x.value): x for x in keywords}
        items_dict = {x.vendor_code: x for x in set(keyword.item for keyword in keywords)}
        positions, errors = parsing.parse_positions(
            [x.item.vendor_code for x in keywords],
            [x.value for x in keywords],
            dest
        )
        errors = {items_dict[vendor_code]: error for vendor_code, error in errors.items()}
        position_objects = [
            models.Position(
                keyword = keywords_dict[key],
                parsing = self.parsing,
                city = city,
                page_capacities = position["page_capacities"],
                page = position["page"],
                position = position["position"],
                promo_page = position["promo_page"],
                promo_position = position["promo_position"],
                sold_out = position["sold_out"]
            ) for key, position in positions.items()
        ]

        models.Position.objects.bulk_create(position_objects)

        return position_objects, errors

    @classmethod
    def get_position_parser_item_dicts(cls, divisor: int, remainder: int) -> list[dict[str, str | int]]:
        book = openpyxl.load_workbook(cls.settings.PARSER_POSITION_DATA_PATH)
        sheet = book.active
        items = {}
        row = 2
        while sheet.cell(row, 1).value:
            item = {
                "vendor_code": int(sheet.cell(row, 1).value),
                "name": sheet.cell(row, 2).value,
                "keyword": sheet.cell(row, 3).value
            }
            items[f"{item['vendor_code']}_{item['keyword']}"] = item
            row += 1

        return [x for x in items.values() if x["vendor_code"] % divisor == remainder]

    @classmethod
    def get_position_parser_keywords(cls, divisor: int, remainder: int) -> list[models.Keyword]:
        customer = core_models.ParserUser.get_customer()
        item_dicts = cls.get_position_parser_item_dicts(divisor, remainder)
        # создание отсутствующих товаров в БД
        items = {
            x["vendor_code"]: models.Item.objects.get_or_create(
                vendor_code = x["vendor_code"],
                user = customer
            )[0] for x in item_dicts
        }

        # todo: переписать с использованием bulk_create
        # https://stackoverflow.com/a/74189912/13186004
        keywords = [
            models.Keyword.objects.update_or_create(
                item = items[x["vendor_code"]],
                item__user = customer,
                value = x["keyword"],
                defaults = {"item_name": x["name"]}
            )[0] for x in item_dicts
        ]
        return keywords

    def run(self, division_remainder: int) -> None:
        keywords_customer = self.get_position_parser_keywords(
            self.settings.PYTEST_XDIST_WORKER_COUNT,
            division_remainder
        )
        keywords = models.Keyword.objects.filter(id__in = (x.id for x in keywords_customer)).prefetch_related(
            "item",
            "item__user"
        )

        # todo: оставить только Москву - временное решение
        for city_dict in [self.settings.MOSCOW_CITY_DICT]:
            city = city_dict["name"]
            dest = city_dict["dest"]
            _, errors = self.parse_positions(keywords, dest, city)
            self.parsing.not_parsed_items.update(errors)

        keywords_to_prepare = tuple(
            x for x in keywords if x.item not in self.parsing.not_parsed_items
            and x.item.user == core_models.ParserUser.get_customer()
        )
        models.PreparedPosition.prepare(keywords_to_prepare)
