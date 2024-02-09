cd ..
CALL venv\Scripts\activate.bat >> logs\seller_api_production.log 2>&1
python parse.py seller_api >> logs\seller_api_production.log 2>&1
