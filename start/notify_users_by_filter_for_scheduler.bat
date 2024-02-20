cd ..
CALL venv\Scripts\activate.bat
python manage.py notify_not_subscribed  >> logs\notify_not_subscribed.log 2>&1
python manage.py notify_without_seller_api_token  >> logs\notify_without_seller_api_token.log 2>&1
