cd ..
CALL venv\Scripts\activate.bat
python manage.py notify_without_seller_api_token  >> logs\notify_without_seller_api_token.log 2>&1
