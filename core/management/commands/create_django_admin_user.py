from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


# todo: поменять пароль
class Command(BaseCommand):
    help = "Создает пользователя с правами администратора"

    def handle(self, *args, **options):
        user = get_user_model()
        if not user.objects.filter(username = "admin").exists():
            user.objects.create_superuser("admin", "", "admin")
        print("The user was created.")
