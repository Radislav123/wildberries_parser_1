cd ..
CALL venv\Scripts\activate.bat >> logs\production.log 2>&1
python parse.py prices false >> logs\production.log 2>&1
