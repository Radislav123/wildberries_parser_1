cd ..
CALL venv\Scripts\activate.bat >> logs\production.log 2>&1
python parse.py positions >> logs\production.log 2>&1
