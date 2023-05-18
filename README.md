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


# Заполнение входных данных парсера

1) [*parser_data/cities.json*](parser_data/cities.json)
    1) все поля берутся из url для запроса поиска на самом сайте
    2) `devtools` => `network` => выполнить поиск по ключевой фразе => название запроса (`Name`) будет начинаться с `search?`, а во вложении
       будут ["data"]["products"]
    3) необходимые поля: `dest`, `regions`, `spp`
        1) вероятно `spp` - это скидка постоянного покупателя
    4) поле `name` необходимо заполнить официальным названием
        1) к примеру, для `Санкт-Петербурга` должно быть `Санкт-Петербург`, а не `Питер`
2) [*parser_data/products.json*](parser_data/items.json)
    1) необходимые поля: `vendor_code`, `keywords`
        1) `vendor_code` - артикул
        2) `leywords` - массив ключевых фраз