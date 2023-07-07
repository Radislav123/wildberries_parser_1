from django.contrib.auth import get_user_model

from core.management.commands import core_command


class Command(core_command.CoreCommand):
    help = "Создает пользователя с правами администратора"

    def handle(self, *args, **options):
        user = get_user_model()
        if not user.objects.filter(username = self.settings.secrets.admin_user.username).exists():
            user.objects.create_superuser(**self.settings.secrets.admin_user.get_dict())
            print("The user was created.")
        else:
            print("The user exists.")
