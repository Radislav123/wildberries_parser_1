cd ..
CALL venv\Scripts\activate.bat >> logs\production.log 2>&1
python manage.py clear_user_history >> logs\production.log 2>&1
