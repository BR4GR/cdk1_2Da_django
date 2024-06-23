
To start postgres from the terminal use the following command:

# Klone das Repository
```bash
git clone https://github.com/BR4GR/cdk1_2Da_django.git
cd cdk1_2Da_django
```

# Erstelle und aktiviere die virtuelle Umgebung
```bash
python3 -m venv cdk1_2Da_env
source cdk1_2Da_env/bin/activate
```

# Installiere Abhängigkeiten
```bash
pip install django_plotly_dash channels daphne redis django-redis channels-redis dpd_static_support pandas numpy openmeteo_requests requests_cache retry_requests
```
# Führe Migrationen durch und erstelle einen Superuser
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

# Starte den Entwicklungsserver
```bash
python manage.py runserver
```

