# MindSight - Local Dev Instructions

1. Create a virtual environment and install dependencies (already added via tooling):

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run migrations and start the dev server:

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

3. Visit http://127.0.0.1:8000/

Note: Settings default to SQLite for easy local development.
