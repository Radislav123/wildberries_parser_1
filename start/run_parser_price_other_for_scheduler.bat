cd ..
CALL venv\Scripts\activate.bat >> logs\prices_other_production.log 2>&1
python parse.py prices false >> logs\prices_other_production.log 2>&1
