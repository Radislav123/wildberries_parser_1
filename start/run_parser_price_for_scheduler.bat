cd ..
CALL venv\Scripts\activate.bat >> logs\prices_production.log 2>&1
python parse.py seller_api >> logs\prices_production.log 2>&1
python manage.py update_personal_sales >> logs\prices_production.log 2>&1
python parse.py prices >> logs\prices_production.log 2>&1
