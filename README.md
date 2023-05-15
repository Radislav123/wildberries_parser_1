# Разное

1) запуск сервера - `python manage.py runserver`
2) запуск парсера - `python manage.py test --keepdb`
3) пока что нет функционала запуска парсера при рабочем сервере => нужно остановить сервер, запустить парсер, снова запустить сервер
4) создание пользователя для административной панели - `python manage.py createsuperuser`
    1) перед созданием пользователя необходимо выполнить миграцию - `python manage.py migrate`
    2) сейчас логин и пароль - `admin` и `admin`
5) название БД - `wildberries_parser_1`
6) города, для которых парсятся товары описаны в [*parser_data/cities.txt*](parser_data/cities.txt)
    1) [*parser_data/cities_example.txt*](parser_data/cities_example.txt) - пример заполнения [*parser_data/cities.txt*](parser_data/cities.txt), и изменяться
       не должен


# Полезные страницы

1) [панель администратора](http://127.0.0.1:8000/admin/) (локально)
