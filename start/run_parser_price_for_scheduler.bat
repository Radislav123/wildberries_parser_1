cd ..
CALL venv\Scripts\activate.bat >> logs\parse_prices.log 2>&1
python parse.py prices >> logs\parse_prices.log 2>&1
