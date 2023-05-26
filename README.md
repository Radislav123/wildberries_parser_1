# Установка

1) установить [*python 3.11*](https://www.python.org/)
2) установить [*PostgreSQL 15*](https://www.postgresql.org/)
3) установить [*git*](https://git-scm.com/downloads)
4) скачать проект
    1) `git clone https://github.com/Radislav123/wildberries_parser_1.git`
        1) репозиторий закрытый, поэтому ссылка имеет вид - `git clone https://<username>:<password>@github.com/username/repository.git`
            1) например `git clone https://Radislav123:strong_password@github.com/username/repository.git`
    2) подготовить проект
        1) заполнить файлы, описанные в пункте [*Заполнение входных данных парсера*](#заполнение-входных-данных-парсера)
        2) заполнить файлы, описанные в пункте [*Секреты*](#секреты)
        3) запустить [*start/prepare_project.bat*](start/prepare_project.bat)
        4) запустить парсер вручную первый раз (первые полученные данные могут быть неверными)
            1) [*start/position_parser.bat*](start/position_parser.bat)
            2) [*start/price_parser.bat*](start/price_parser.bat)
        5) [*настроить периодический запуск парсера*](https://www.windowscentral.com/how-create-automated-task-using-task-scheduler-windows-10)
            1) программа - `python` (19 пункт)
            2) аргументы - `run.py positions` (20 пункт)
            3) папка - папка проекта (21 пункт)
    3) запустить локальный сервер - раздел [*Разное*](#разное) пункт 1
        2) запуск сервера необходим для доступа к [*административной панели*](http://127.0.0.1:8000/admin/)
        3) сервер необходимо запускать каждый раз после перезапуска компьютера, чтобы получить доступ к
           [*административной панели*](http://127.0.0.1:8000/admin/)


# Заполнение входных данных парсера

1) [*parser_data/cities.json*](parser_data/cities.json)
    1) заполнять не нужно, так как уже заполнено
    2) если все же нужно
        1) поле `name` необходимо заполнить официальным названием
            1) к примеру, для `Санкт-Петербурга` должно быть `Санкт-Петербург`, а не `Питер`
2) [*parser_data/position_parser_data.xlsx*](parser_data/position_parser_data.xlsx)
    1) пример заполнения - [*parser_data/position_parser_data_example.xlsx*](parser_data/position_parser_data_example.xlsx)
3) [*parser_data/price_parser_data.xlsx*](parser_data/price_parser_data.xlsx)
    1) пример заполнения - [*parser_data/price_parser_data_example.xlsx*](parser_data/price_parser_data_example.xlsx)


# Секреты

1) [*база данных*](https://www.postgresql.org/)
    1) скопировать [*secrets/database/credentials_example.json*](secrets/database/credentials_example.json) в ту же папку, но назвать `credentials.json`
    2) заполнить `USER` и `PASSWORD`, которые указывались при установке [*postgres*](https://www.postgresql.org/)
    3) [*создать БД*](https://www.tutorialspoint.com/postgresql/postgresql_create_database.htm) и указать ее название в поле `NAME`
        1) `CREATE DATABASE wildberries_parser_1;`
2) [*геопарсер*](https://positionstack.com/)
    1) скопировать [*secrets/geoparser/credentials_example.json*](secrets/geoparser/credentials_example.json) в ту же папку, но назвать `credentials.json`
    2) для работы парсера нужно только поле `api_key`


# Разное

1) запуск сервера
    1) в обычном режиме - [*start/runserver.bat*](start/runserver.bat)
    2) в фоновом режиме - [*start/runserver_background.bat*](start/runserver_background.bat)
2) запуск парсера
    1) запуск парсера позиций - [*start/position_parser.bat*](start/position_parser.bat)
    2) запуск парсера цен - [*start/price_parser.bat*](start/price_parser.bat)
    3) чтобы только проверить, что выбираются нужные тесты - `python run.py prices --collect-only`
    4) в конце команды можно добавлять любые аргументы `pytest`
        1) они перезапишут те, что определены в [*parser_project/project_settings.py*](parser_project/project_settings.py) `PYTEST_ARGS`
        2) пример - `python run.py prices --collect-only`
3) до запуска парсера не получится зайти в административную панель
    1) перед первым запуском парсера необходимо выполнить миграцию - `python manage.py migrate`
    2) сейчас логин и пароль - `admin` и `admin`
        1) смотреть [*run.py*](run.py) `before_pytest`
4) скачать excel-файл - открыть таблицу в панели администратора => отметить галочкой необходимые объекты => в поле `Action` выбрать `Download ... excel` =>
   нажать `Go`
5) первый поиск может давать неправильные результаты
6) [панель администратора](http://127.0.0.1:8000/admin/) (локально)


