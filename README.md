# Разное

1) запуск сервера - `python manage.py runserver`
2) запуск парсера - `python manage.py test --keepdb`
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

1) почта [*Рамблер*](https://www.rambler.ru/)
    1) логин и пароль - [*secrets/mail/credentials.txt*](secrets/mail/credentials.txt)
2) сервис [*SMS-Activate*](https://sms-activate.org/) - виртуальные сим-карты
    1) логин и пароль - [*secrets/sms_activate/credentials.txt*](secrets/sms_activate/credentials.txt)
    2) api-ключ - [*secrets/sms_activate/api_key.txt*](secrets/sms_activate/api_key.txt)
3) [*Wildberries*](https://www.wildberries.ru/)
    1) cookie для авторизации - [*secrets/wildberries/auth_cookie.txt*](secrets/wildberries/auth_cookie.txt)


# Авторизация на Wildberries

1) cookie для авторизации может понадобиться обновлять
    1) по их истечению - срок у текущей - `2024-05-15T12:51:08.671Z`
    2) при прочих проблемах с авторизацией

## Замена cookie для авторизации

1) [*как найти cookie*](https://cookie-script.com/blog/chrome-cookies)
2) необходимая называется `WILDAUTHNEW_V3`
3) необходимо заменить вторую строку в [*secrets/wildberries/auth_cookie.txt*](secrets/wildberries/auth_cookie.txt) на значение из браузера (столбец `Value`)
