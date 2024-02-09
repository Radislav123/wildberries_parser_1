cd ..
CALL venv\Scripts\activate.bat >> logs\positions_production.log 2>&1
python parse.py positions >> logs\positions_production.log 2>&1
