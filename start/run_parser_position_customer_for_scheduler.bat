cd ..
CALL venv\Scripts\activate.bat >> logs\production.log 2>&1
python parse.py positions true >> logs\production.log 2>&1
