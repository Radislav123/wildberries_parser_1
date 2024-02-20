cd ..
CALL venv\Scripts\activate.bat >> logs\parse_positions.log 2>&1
python parse.py positions >> logs\parse_positions.log 2>&1
