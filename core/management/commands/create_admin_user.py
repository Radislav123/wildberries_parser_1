from django.contrib.auth import get_user_model

from core.management.commands import core_command


class Command(core_command.CoreCommand):
    help = "Создает пользователя с правами администратора"

    def handle(self, *args, **options):
        user_model = get_user_model()
        if not user_model.objects.filter(username = self.settings.secrets.customer_user.username).exists():
            user_model.objects.create_superuser(**self.settings.secrets.customer_user.get_dict())
            print("The user was created.")
        else:
            print("The user exists.")
