"""Restablece exclusivamente un entorno E2E previamente preparado."""
import json
import shutil

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from .preparar_e2e import Command as Preparar


class Command(BaseCommand):
    help = 'Restablece los datos desechables antes de un caso E2E.'
    requires_system_checks = []

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != 'config.settings_e2e':
            raise CommandError('Solo se permite config.settings_e2e.')
        base = settings.DATABASES['default']
        directorio = settings.E2E_DIR
        manifiesto = directorio / 'datos-e2e.json'
        if (base['ENGINE'] != 'django.db.backends.postgresql'
                or base['HOST'] != '127.0.0.1'
                or not (base['NAME'] == 'conecta_e2e' or base['NAME'].startswith('conecta_e2e_'))
                or settings.STORAGES['default']['BACKEND'] != 'django.core.files.storage.FileSystemStorage'):
            raise CommandError('Se requiere PostgreSQL y almacenamiento locales de E2E.')
        try:
            datos = json.loads(manifiesto.read_text())
        except (OSError, ValueError) as error:
            raise CommandError('Ejecuta preparar_e2e en un entorno nuevo primero.') from error
        if datos.get('base') != base['NAME']:
            raise CommandError('El manifiesto no corresponde a esta base E2E.')
        for nombre in ('media', 'correos'):
            if (directorio / nombre).is_symlink():
                raise CommandError('No se permite limpiar enlaces simbolicos.')
        # Solo se vacia la base desechable validada; nunca la configuracion habitual.
        call_command('flush', interactive=False, verbosity=0)
        for nombre in ('media', 'correos'):
            ruta = directorio / nombre
            if ruta.exists():
                shutil.rmtree(ruta)
        with transaction.atomic():
            datos = Preparar().crear_datos()
        datos['base'] = base['NAME']
        manifiesto.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n')
        self.stdout.write('Datos E2E restablecidos.')
