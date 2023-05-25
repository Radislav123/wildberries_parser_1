cd ..
pip install -r requirements.txt
python manage.py makemigrations parser
python manage.py migrate
pause
