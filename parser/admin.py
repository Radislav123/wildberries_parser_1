from django.contrib import admin

from .models import ProjectModel


# Register your models here.
for model in ProjectModel.__subclasses__():
    admin.site.register(model)
