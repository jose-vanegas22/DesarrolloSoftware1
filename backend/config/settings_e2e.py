"""Configuracion exclusiva para servidores E2E locales y de CI."""
from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403
from .postgres_pruebas import base_postgresql


# Una carpeta nueva por ejecucion aisla los PDF, correos y datos de referencia.
directorio = os.environ.get('CONECTA_E2E_DIR')
if not directorio or not Path(directorio).is_absolute() or not Path(directorio).is_dir():
    raise ImproperlyConfigured(
        'Define CONECTA_E2E_DIR con una carpeta temporal existente y una ruta absoluta.'
    )
E2E_DIR = Path(directorio).resolve()

SECRET_KEY = 'clave-ficticia-exclusiva-del-entorno-e2e-local'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
ROOT_URLCONF = 'config.urls_e2e'
nombre_base = os.environ.get('CONECTA_E2E_DB_NAME', 'conecta_e2e')
if not (nombre_base == 'conecta_e2e' or nombre_base.startswith('conecta_e2e_')):
    raise ImproperlyConfigured('La base E2E debe llamarse conecta_e2e o empezar por conecta_e2e_.')
DATABASES = {'default': base_postgresql(nombre_base)}
MEDIA_ROOT = E2E_DIR / 'media'
MEDIA_URL = '/media/'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        # El frontend sirve en otro puerto y necesita un enlace absoluto al PDF.
        'OPTIONS': {'base_url': 'http://127.0.0.1:8000/media/'},
    },
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.filebased.EmailBackend',
        'OPTIONS': {'file_path': E2E_DIR / 'correos'},
    },
}
DEFAULT_FROM_EMAIL = 'Conecta E2E <no-responder@conecta.test>'
FRONTEND_URL = 'http://localhost:5173'
CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']

# Clave publica de pruebas v2 publicada por Google; no es una credencial privada.
# Se conserva la consulta real a Google: este entorno aun necesita red para CAPTCHA.
RECAPTCHA_SECRET_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
