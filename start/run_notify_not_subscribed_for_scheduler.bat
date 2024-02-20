cd ..
CALL venv\Scripts\activate.bat
python manage.py notify_not_subscribed  >> logs\notify_not_subscribed.log 2>&1
