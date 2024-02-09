cd ..
CALL venv\Scripts\activate.bat
python parse.py seller_api
python manage.py update_personal_sales
python parse.py prices
pause
