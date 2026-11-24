"""Conexion a un PostgreSQL local desechable, sin leer credenciales de Supabase."""
import os


def base_postgresql(nombre):
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': nombre,
        # El servidor se ejecuta en la maquina local o en un servicio del runner.
        'HOST': '127.0.0.1',
        'PORT': os.environ.get('CONECTA_TEST_DB_PORT', '5432'),
        'USER': os.environ.get('CONECTA_TEST_DB_USER', 'conecta_test'),
        'PASSWORD': os.environ.get('CONECTA_TEST_DB_PASSWORD', 'conecta_test_local'),
    }
