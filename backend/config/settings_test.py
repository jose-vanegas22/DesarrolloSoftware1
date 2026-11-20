"""Pruebas locales con --settings=config.settings_test; no usar para runserver.

No requiere crear una base en Supabase ni completar credenciales en este archivo.
SQLite permite comprobar la logica, pero no los bloqueos de PostgreSQL.
"""
from .settings import *  # noqa: F403

# Valor ficticio para la firma de Django/JWT durante las pruebas.
# No es una contraseña de PostgreSQL ni una clave de Supabase.
# Se sustituye la SECRET_KEY del entorno real para no usarla en los tests.
SECRET_KEY = 'clave-exclusiva-para-pruebas-locales'

# Sustituye toda la conexion PostgreSQL heredada, incluidas sus credenciales.
# La base de pruebas vive en memoria y se descarta al terminar la ejecucion.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

# Los archivos de prueba tampoco se suben al bucket compartido de Supabase.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
