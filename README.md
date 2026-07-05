# Dharm Raksha Sangh

Django project scaffold for the **Dharm Raksha Sangh** site.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The project package is named `dharm_raksha_sangh` because Python packages cannot contain spaces.
