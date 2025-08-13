# user_auth_app/admin.py
from django.contrib import admin
from django.apps import apps

# Alle Models der aktuellen App holen
app = apps.get_app_config('user_auth_app')

# Jedes Model registrieren (falls noch nicht registriert)
for model_name, model in app.models.items():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
