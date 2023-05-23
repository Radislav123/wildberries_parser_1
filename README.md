# Разное

1) запуск сервера - `python manage.py runserver`
2) запуск парсера - `python run.py [positions | prices]`
    1) `positions` - запускается парсер позиций
    2) `prices` - запускается парсер цен
    3) чтобы только проверить, что выбираются нужные тесты - `python run.py prices --collect-only`
    4) в конце команды можно добавлять любые аргументы `pytest`
        1) они перезапишут те, что определены в [*parser_project/project_settings.py*](parser_project/project_settings.py) `PYTEST_ARGS`
        2) пример - `python run.py prices --collect-only`
3) до запуска парсера не получится зайти в административную панель
    1) перед первым запуском парсера необходимо выполнить миграцию - `python manage.py migrate`
    2) сейчас логин и пароль - `admin` и `admin`
        1) смотреть [*run.py*](run.py) `before_pytest`
4) все файлы, содержащие данные для парсинга или авторизаций, заполняются следующим образом
    1) разделитель - перенос строки, никаких дополнительных разделителей => каждая порция информации с новой строки
    2) в конце файла пустая строка
5) скачать excel-файл - открыть таблицу в панели администратора => отметить галочкой необходимые объекты => в поле `Action` выбрать `Download ... excel` =>
   нажать `Go`
6) первый поиск может давать неправильные результаты
7) [панель администратора](http://127.0.0.1:8000/admin/) (локально)


# Секреты

1) [*база данных*](https://www.postgresql.org/)
    1) скопировать [*secrets/database/credentials_example.json*](secrets/database/credentials_example.json) в ту же папку, но назвать `credentials.json`
    2) заполнить `USER` и `PASSWORD`, которые указывались при установке [*postgres*](https://www.postgresql.org/)
    3) создать БД и указать ее название в поле `NAME`


# Заполнение входных данных парсера

1) [*parser_data/cities.json*](parser_data/cities.json)
    1) заполнять не нужно, так как уже заполнено
    2) все поля берутся из url для запроса поиска на самом сайте
    3) `devtools` => `network` => выполнить поиск по ключевой фразе => название запроса (`Name`) будет начинаться с `search?`, а во вложении
       будут ["data"]["products"]
    4) необходимые поля: `dest`, `regions`
    5) поле `name` необходимо заполнить официальным названием
        1) к примеру, для `Санкт-Петербурга` должно быть `Санкт-Петербург`, а не `Питер`
2) [*parser_data/position_parser_data.xlsx*](parser_data/position_parser_data.xlsx)
    1) пример заполнения - [*parser_data/position_parser_data_example.xlsx*](parser_data/position_parser_data_example.xlsx)
3) [*parser_data/price_parser_data.xlsx*](parser_data/price_parser_data.xlsx)
    1) пример заполнения - [*parser_data/price_parser_data_example.xlsx*](parser_data/price_parser_data_example.xlsx)


# Установка

1) установить [*python 3.11*](https://www.python.org/)
2) установить [*PostgreSQL 15*](https://www.postgresql.org/)
3) установить [*git*](https://git-scm.com/downloads)
4) скачать проект
    1) `git clone https://github.com/Radislav123/wildberries_parser_1.git`
    2) подготовить проект
        1) заполнить файлы, описанные в пункте [*Заполнение входных данных парсера*](#заполнение-входных-данных-парсера)
        2) заполнить файлы, описанные в пункте [*Секреты*](#секреты)
        3) выполнить (в командной строке из папки проекта)
            ```commandline
            python install -r requirements.txt
            python manage.py makemigrations parser
            python manage.py migrate
            ```
        4) запустить парсер вручную первый раз (первые полученные данные могут быть неверными)
            1) `python run.py positions`
            2) `python run.py prices`
        5) [*настроить периодический запуск парсера*](https://www.windowscentral.com/how-create-automated-task-using-task-scheduler-windows-10)
            1) программа - `python` (19 пункт)
            2) аргументы - `run.py positions` (20 пункт)
            3) папка - папка проекта (21 пункт)
    3) запустить локальный сервер - `python manage.py runserver`
        1) если надо запустить фоново - `START /B python manage.py runserver`
        2) запуск сервера необходим для доступа к [*административной панели*](http://127.0.0.1:8000/admin/)
        3) сервер необходимо запускать каждый раз после перезапуска компьютера, чтобы получить доступ к
           [*административной панели*](http://127.0.0.1:8000/admin/)
