from django.contrib.auth import get_user_model


# todo: убрать создание админа отсюда или поменять ему пароль
def run():
    user = get_user_model()
    if not user.objects.filter(username = "admin").exists():
        user.objects.create_superuser("admin", "", "admin")
