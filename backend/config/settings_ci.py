"""Pruebas del backend contra PostgreSQL; requiere un servidor local desechable."""
from .settings_test import *  # noqa: F403
from .postgres_pruebas import base_postgresql


DATABASES = {'default': base_postgresql('conecta_ci')}
# El runner crea esta base, aplica migraciones y la elimina al terminar.
DATABASES['default']['TEST'] = {'NAME': 'test_conecta_ci'}

# El aislamiento incluye el correo, aunque exista un .env local con SMTP real.
MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}}
