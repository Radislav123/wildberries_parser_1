# Разное

1) запуск сервера - `python manage.py runserver`
2) запуск парсера - `python run.py`
    1) чтобы только проверить, что выбираются нужные тесты - `python run.py --collect-only`
    2) в конце команды можно добавлять любые аргументы `pytest`
        1) они перезапишут те, что определены в [*parser_project/project_settings.py*](parser_project/project_settings.py) `PYTEST_ARGS`
        2) пример - `python run.py --collect-only`
3) пока что нет функционала запуска парсера при рабочем сервере => нужно остановить сервер, запустить парсер, снова запустить сервер
4) создание пользователя для административной панели - `python manage.py createsuperuser`
    1) перед созданием пользователя необходимо выполнить миграцию - `python manage.py migrate`
    2) сейчас логин и пароль - `admin` и `admin`
5) название БД - `wildberries_parser_1`
6) все файлы, содержащие данные для парсинга или авторизаций, заполняются следующим образом
    1) разделитель - перенос строки, никаких дополнительных разделителей => каждая порция информации с новой строки
    2) в конце файла пустая строка
7) города, для которых парсятся товары описаны в [*parser_data/cities.txt*](parser_data/cities.txt)


# Полезные страницы

1) [панель администратора](http://127.0.0.1:8000/admin/) (локально)


# Секреты

1) [*Wildberries*](https://www.wildberries.ru/)
    1) cookie для авторизации - [*secrets/wildberries/auth_cookie.txt*](secrets/wildberries/auth_cookie.txt)


# Авторизация на Wildberries

1) cookie для авторизации может понадобиться обновлять
    1) по их истечению - срок у текущей - `2024-05-15T12:51:08.671Z`
    2) при прочих проблемах с авторизацией

## Замена cookie для авторизации

1) [*как найти cookie*](https://cookie-script.com/blog/chrome-cookies)
2) необходимая называется `WILDAUTHNEW_V3`
3) необходимо заменить вторую строку в [*secrets/wildberries/auth_cookie.txt*](secrets/wildberries/auth_cookie.txt) на значение из браузера (столбец `Value`)
