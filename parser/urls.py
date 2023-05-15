# urls.py
from django.urls import path

from .views import CheckView


urlpatterns = [
    path(CheckView.url, CheckView.as_view()),
]
