cd ..
CALL venv\Scripts\activate.bat >> logs\seller_api_other_production.log 2>&1
python parse.py seller_api false >> logs\seller_api_other_production.log 2>&1
