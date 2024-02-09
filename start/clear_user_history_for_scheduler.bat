cd ..
CALL venv\Scripts\activate.bat >> logs\clear_user_history_production.log 2>&1
python manage.py clear_user_history >> logs\clear_user_history_production.log 2>&1
