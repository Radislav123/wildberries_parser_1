cd ..
CALL venv\Scripts\activate.bat >> logs\prices_production.log 2>&1
python parse.py prices >> logs\prices_production.log 2>&1
