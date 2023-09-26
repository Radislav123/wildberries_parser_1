import openpyxl

from core import models as core_models, parser as parser_core, service
from pages import MainPage
from . import models, settings


City = dict[str, str]


class Parser(parser_core.Parser):
    settings = settings.Settings()
    parsing_type = "position"

    def parse_positions(
            self,
            keywords: list[models.Keyword],
            dest: str,
            regions: str,
            city: str
    ) -> tuple[list[models.Position], dict[models.Item, Exception]]:
        keywords_dict = {(x.item.vendor_code, x.value): x for x in keywords}
        items_dict = {x.vendor_code: x for x in set(keyword.item for keyword in keywords)}
        positions, errors = service.parse_positions(
            [x.item.vendor_code for x in keywords], [x.value for x in keywords], dest, regions
        )
        errors = {items_dict[vendor_code]: error for vendor_code, error in errors.items()}
        position_objects = [
            models.Position(
                keyword = keywords_dict[key],
                parsing = self.parsing,
                city = city,
                page_capacities = position["page_capacities"],
                page = position["page"],
                value = position["position"]
            ) for key, position in positions.items()
        ]

        models.Position.objects.bulk_create(position_objects)

        return position_objects, errors

    @classmethod
    def get_position_parser_item_dicts(cls) -> list[dict[str, str | int]]:
        book = openpyxl.load_workbook(cls.settings.PARSER_POSITION_DATA_PATH)
        sheet = book.active
        items = []
        row = 2
        while sheet.cell(row, 1).value:
            items.append(
                {
                    "vendor_code": int(sheet.cell(row, 1).value),
                    "name": sheet.cell(row, 2).value,
                    "keyword": sheet.cell(row, 3).value
                }
            )
            row += 1
        return items

    @classmethod
    def get_position_parser_keywords(cls) -> list[models.Keyword]:
        item_dicts = cls.get_position_parser_item_dicts()
        # создание отсутствующих товаров в БД
        items = {
            x["vendor_code"]: models.Item.objects.get_or_create(
                vendor_code = x["vendor_code"],
                user = core_models.ParserUser.get_customer()
            )[0] for x in item_dicts
        }

        keywords = [
            models.Keyword.objects.update_or_create(
                item = items[x["vendor_code"]],
                item__user = core_models.ParserUser.get_customer(),
                value = x["keyword"],
                defaults = {"item_name": x["name"]}
            )[0] for x in item_dicts
        ]
        return keywords

    def run_customer(self, city_dict: City) -> None:
        keywords = self.get_position_parser_keywords()
        self.run(keywords, city_dict, True)

    def run_other(self, city_dict: City) -> None:
        raise NotImplementedError()

    def run(self, keywords: list[models.Keyword], city_dict: City, prepare_table: bool) -> None:
        main_page = MainPage(self)
        main_page.open()
        dest, regions = main_page.set_city(city_dict)
        city = city_dict["name"]
        _, errors = self.parse_positions(keywords, dest, regions, city)
        self.parsing.not_parsed_items = errors

        if prepare_table:
            models.PreparedPosition.prepare(keywords, city)
