cd ..
CALL venv\Scripts\activate.bat >> logs\production.log 2>&1
python parse.py prices >> logs\production.log 2>&1
