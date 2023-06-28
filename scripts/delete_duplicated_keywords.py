from django.db import models as django_models

from parser import models


def get_duplicates() -> dict:
    duplicates = models.Keyword.objects.values("value", "item_id").annotate(
        value_count = django_models.Count("value")
    ).filter(value_count__gt = 1)
    return duplicates


def get_ids_to_remove(duplicates: dict) -> list[int]:
    ids = [models.Keyword.objects.filter(value = obj["value"], item_id = obj["item_id"]).order_by("id").last().id for
           obj in duplicates]
    return ids


def run():
    for obj_id in get_ids_to_remove(get_duplicates()):
        models.Keyword.objects.get(id = obj_id).delete()
        print(f"{models.Keyword.__name__} {obj_id} was deleted")
