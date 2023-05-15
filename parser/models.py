from django.db import models


class ProjectModel(models.Model):
    class Meta:
        abstract = True


class Item(ProjectModel):
    vendor_code = models.PositiveIntegerField()
