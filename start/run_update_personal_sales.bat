cd ..
CALL venv\Scripts\activate.bat >> logs\update_personal_sales_production.log 2>&1
python manage.py update_personal_sales >> logs\update_personal_sales_production.log 2>&1
