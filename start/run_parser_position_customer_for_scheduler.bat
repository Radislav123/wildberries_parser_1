cd ..
CALL venv\Scripts\activate.bat >> logs\positions_customer_production.log 2>&1
python parse.py positions true >> logs\positions_customer_production.log 2>&1
