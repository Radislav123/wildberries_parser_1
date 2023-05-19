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
        1) смотреть [*run.py*](run.py) `before_pytest`
5) название БД - `wildberries_parser_1`
6) все файлы, содержащие данные для парсинга или авторизаций, заполняются следующим образом
    1) разделитель - перенос строки, никаких дополнительных разделителей => каждая порция информации с новой строки
    2) в конце файла пустая строка
7) скачать excel-файл - открыть таблицу в панели администратора => отметить галочкой необходимые объекты => в поле `Action` выбрать `Download excel` =>
   нажать `Go`
8) первый поиск может давать неправильные результаты


# Полезные страницы

1) [панель администратора](http://127.0.0.1:8000/admin/) (локально)


# Секреты

1) [*Wildberries*](https://www.wildberries.ru/)
    1) cookie для авторизации - [*secrets/wildberries/auth_cookie.txt*](secrets/wildberries/auth_cookie.txt)
    2) заполнение
        1) скопировать [*secrets/wildberries/auth_cookie_example.txt*](secrets/wildberries/auth_cookie_example.txt) в ту же папку, но назвать `auth_cookies.txt`
        2) [*как найти cookie*](https://cookie-script.com/blog/chrome-cookies)
        3) необходимая называется `WILDAUTHNEW_V3`
        4) заменить вторую строку в [*secrets/wildberries/auth_cookie.txt*](secrets/wildberries/auth_cookie.txt) на значение из браузера (столбец `Value`)
2) [*база данных*](https://www.postgresql.org/)
    1) скопировать [*secrets/database/credentials_example.json*](secrets/database/credentials_example.json) в ту же папку, но назвать `credentials.json`
    2) заполнить `USER` и `PASSWORD`, которые указывались при установке [*postgres*](https://www.postgresql.org/)
    3) создать БД и указать ее название в поле `NAME`


# Авторизация на Wildberries

1) cookie для авторизации может понадобиться обновлять
    1) по их истечению - срок у текущей - `2024-05-15T12:51:08.671Z`
    2) при прочих проблемах с авторизацией


# Заполнение входных данных парсера

1) [*parser_data/cities.json*](parser_data/cities.json)
    1) все поля берутся из url для запроса поиска на самом сайте
    2) `devtools` => `network` => выполнить поиск по ключевой фразе => название запроса (`Name`) будет начинаться с `search?`, а во вложении
       будут ["data"]["products"]
    3) необходимые поля: `dest`, `regions`, `spp`
        1) вероятно `spp` - это скидка постоянного покупателя
    4) поле `name` необходимо заполнить официальным названием
        1) к примеру, для `Санкт-Петербурга` должно быть `Санкт-Петербург`, а не `Питер`
2) [*parser_data/items.json*](parser_data/items.json)
    1) необходимые поля: `vendor_code`, `keywords`
        1) `vendor_code` - артикул
        2) `leywords` - массив ключевых фраз


# Установка

1) установить [*python 3.11*](https://www.python.org/)
2) установить [*PostgreSQL 15*](https://www.postgresql.org/)
3) установить [*git*](https://git-scm.com/downloads)
4) скачать проект
    1) `git clone https://github.com/Radislav123/wildberries_parser_1.git`
    2) подготовить проект
        1) заполнить файлы, описанные в пункте [*Заполнение входных данных парсера*](#заполнение-входных-данных-парсера)
        2) заполнить файлы, описанные в пункте [*Секреты*](#секреты)
        3) выполнить
            ```commandline
            python install -r requirements.txt
            python manage.py makemigrations parser
            python manage.py migrate
            ```
        4) запустить парсер вручную первый раз (первые полученные данные могут быть неверными)
            1) `python run.py`
        5) [*настроить периодический запуск парсера*](https://www.windowscentral.com/how-create-automated-task-using-task-scheduler-windows-10)
            1) программа - `python` (19 пункт)
            2) аргументы - `run.py` (20 пункт)
            3) папка - папка с проектом (21 пункт)
    3) запустить локальный сервер - `python manage.py runserver`
        1) если надо запустить фоново - `START /B python manage.py runserver`
        2) запуск сервера необходим для доступа к [*административной панели*](http://127.0.0.1:8000/admin/)
        3) сервер необходимо запускать каждый раз после перезапуска компьютера, чтобы получить доступ к
           [*административной панели*](http://127.0.0.1:8000/admin/)
