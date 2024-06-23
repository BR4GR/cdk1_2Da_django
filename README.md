
# Instalation

```bash
sudo apt update
```
```bash
sudo apt upgrade -y
```
```bash
sudo apt install git python3 python3-venv python3-pip -y
```

### Klone das Repository
```bash
git clone https://github.com/BR4GR/cdk1_2Da_django.git
```
```bash
cd cdk1_2Da_django
``` 

### Erstelle und aktiviere die virtuelle Umgebung
```bash
python3 -m venv cdk1_2Da_env
```
```bash
source cdk1_2Da_env/bin/activate
```

### Installiere Abhängigkeiten
```bash
pip install django_plotly_dash channels daphne redis django-redis channels-redis dpd_static_support pandas numpy openmeteo_requests requests_cache retry_requests
```
### Führe Migrationen durch und erstelle einen Superuser
```bash
python manage.py makemigrations
```
```bash
python manage.py migrate
```
```bash
python manage.py createsuperuser
```

### Starte den Entwicklungsserver
```bash
python manage.py runserver
```

http://127.0.0.1:8000/klimadaten/