# Установка

1) установить [*python 3.11*](https://www.python.org/)
2) установить [*PostgreSQL 15*](https://www.postgresql.org/)
3) установить [*git*](https://git-scm.com/downloads)
4) скачать проект
    1) `git clone https://github.com/Radislav123/wildberries_parser_1.git`
        1) репозиторий закрытый, поэтому ссылка имеет вид - `git clone https://<username>:<token>@github.com/username/repository.git`
            1) например `git clone https://Radislav123:real_token@github.com/username/repository.git`
    2) подготовить проект
        1) заполнить файлы, описанные в пункте [*Заполнение входных данных парсера*](#заполнение-входных-данных-парсера)
        2) заполнить файлы, описанные в пункте [*Секреты*](#секреты)
        3) выполнить миграции
            1)
           ```commandline
           python manage.py makemigrations core parser_price parser_position
           python manage.py migrate
           ```
        4) запустить парсер вручную первый раз (первые полученные данные могут быть неверными)
            1) [*start/position_parser.bat*](start/run_parser_position.bat)
            2) [*start/price_parser.bat*](start/run_parser_price.bat)
        5) [*настроить периодический запуск парсера*](https://www.windowscentral.com/how-create-automated-task-using-task-scheduler-windows-10)
            1) программа - `python` (19 пункт)
            2) аргументы - `run.py positions` (20 пункт)
            3) папка - папка проекта (21 пункт)
    3) запустить локальный сервер - раздел [*Разное*](#разное) пункт 1
        1) запуск сервера необходим для доступа к [*административной панели*](http://127.0.0.1:8000/admin/)


# Заполнение входных данных парсера

1) [*parsing_data/cities.json*](parsing_data/cities.json)
    1) заполнять не нужно, так как уже заполнено
    2) если все же нужно
        1) поле `name` необходимо заполнить официальным названием
            1) к примеру, для `Санкт-Петербурга` должно быть `Санкт-Петербург`, а не `Питер`
        2) поле `label` - отображаемое название
2) [*parsing_data/parser_position.xlsx*](parsing_data/parser_position.xlsx)
    1) пример заполнения - [*parsing_data/parser_position_example.xlsx*](parsing_data/parser_position_example.xlsx)
3) [*parsing_data/parser_position.xlsx*](parsing_data/parser_position.xlsx)
    1) пример заполнения - [*parsing_data/parser_position_example.xlsx*](parsing_data/parser_position_example.xlsx)


# Секреты

1) все секреты заполняются одинаково
    1) скопировать `secrets/folder_name/secret_file.json` в ту же папку, но убрать из названия `example`
        1) `credentials_example.json` -> `credentials.json`
2) специально для [*secrets/database/credentials.json*](secrets/database/credentials.json)
    1) заполнить `USER` и `PASSWORD`, которые указывались при установке [*postgres*](https://www.postgresql.org/)
    2) [*создать БД*](https://www.tutorialspoint.com/postgresql/postgresql_create_database.htm) и указать ее название в поле `NAME`
        1) `CREATE DATABASE wildberries_parser_1;`


# Разное

1) запуск сервера [*start/runserver.bat*](start/runserver.bat)
2) запуск парсера
    1) запуск парсера позиций - [*start/run_parser_position.bat*](start/run_parser_position.bat)
        1) `python parse.py positions`
    2) запуск парсера цен - [*start/run_parser_price.bat*](start/run_parser_price.bat)
        1) `python parse.py prices`
    3) чтобы только проверить, что выбираются нужные тесты - `python parse.py prices --collect-only`
    4) в конце команды можно добавлять любые аргументы `pytest`
        1) они перезапишут те, что определены в `PYTEST_ARGS`
           [*parser_price/settings.py*](parser_price/settings.py) или [*parser_position/settings.py*](parser_position/settings.py)
        2) пример - `python parse.py prices --collect-only`
3) для создания в административной панели пользователя с правами администратора необходимо выполнить
   [*core/management/commands/create_admin_user.py*](core/management/commands/create_admin_user.py)
    1) `python manage.py create_admin_user`
    2) администраторские логин и пароль по умолчанию находятся в [*secrets/admin_panel/admin_user.json*](secrets/admin_panel/admin_user.json)
4) скачать excel-файл - открыть таблицу в панели администратора => отметить галочкой необходимые объекты => в поле `Action` выбрать `Download ... excel` =>
   нажать `Go`
5) [панель администратора](http://127.0.0.1:8000/admin/) (локально)
6) для возможности парсинга цен необходимо авторизоваться в окне, открываемом командой
   [*parser_price/management/commands/run_wildberries_log_in_window.py*](parser_price/management/commands/run_wildberries_log_in_window.py)
    1) `python manage.py run_wildberries_log_in_window`
    2) без открытого окна с авторизованным аккаунтом `wildberries` парсинг цен будет ломаться
7) для работы скриптов в [*db_dumps/*](db_dumps) без запрашивания пароля, необходимо установить переменную окружения
   `PGPASSWORD` с паролем от пользователя `Postgres`, указанного в переменной `USERNAME` в скрипте
