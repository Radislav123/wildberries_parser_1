cd ..
CALL venv\Scripts\activate.bat
python parse.py seller_api
python parse.py prices
python manage.py update_personal_sales
pause
