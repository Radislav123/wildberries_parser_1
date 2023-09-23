cd ..
CALL venv\Scripts\activate.bat >> logs\prices_customer_production.log 2>&1
python parse.py prices true >> logs\prices_customer_production.log 2>&1
