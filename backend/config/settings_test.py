"""Pruebas locales aisladas: no usan la base compartida ni Supabase Storage."""
from .settings import *  # noqa: F403

SECRET_KEY = 'clave-exclusiva-para-pruebas-locales'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
