cd ..
CALL venv\Scripts\activate.bat >> logs\seller_api_customer_production.log 2>&1
python parse.py seller_api true >> logs\seller_api_customer_production.log 2>&1
