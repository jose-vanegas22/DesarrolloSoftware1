"""Crea las precondiciones del inventario E2E en un entorno nuevo y local."""
import json
from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import BaseCommand, CommandError, call_command
from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils import timezone

from apps.articulos.models import Articulo, Autor, VersionArticulo
from apps.eventos.models import Evento, FechaLimite
from apps.usuarios.models import Usuario


PASSWORD_COMUN = 'ClaveSegura123'
PDF_PRUEBA = b'%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n'

# Coinciden con los recorridos existentes. Son cuentas nuevas en PostgreSQL local;
# no se consulta ni modifica ninguna cuenta compartida del equipo.
CUENTAS = (
    ('login', 'autor.valencia@prueba1.com', '@Valencia1', 'Autor', 'Login', ('autor',)),
    ('bloqueo', 'autor.valencia@prueba2.com', '@Valencia2', 'Autor', 'Bloqueo', ('autor',)),
    ('multirrol', 'autor.valencia@prueba2.2.com', '@Valencia3', 'Autor', 'Comite', ('autor', 'comite')),
    ('autor_jose', 'autor.jose@prueba.com', PASSWORD_COMUN, 'Jose', 'Prueba', ('autor',)),
    ('autor_miguel', 'autor.miguel@prueba.com', PASSWORD_COMUN, 'Miguel', 'Prueba', ('autor',)),
    ('comite_cristian', 'comite.cristian@prueba.com', PASSWORD_COMUN, 'Cristian', 'Comite', ('comite',)),
    ('autor_consulta', 'juandavid@teste2e.com', PASSWORD_COMUN, 'Juan David', 'Salazar', ('autor',)),
    ('comite_consulta', 'juan.salazar.caicedo@correunivalle.edu.co', PASSWORD_COMUN, 'Juan', 'Comite', ('comite',)),
    ('autor_protegido', 'cristian.madero@correounivalle.edu.co', PASSWORD_COMUN, 'Cristian', 'Autor', ('autor',)),
    ('administrador', 'admin@e2e.test', PASSWORD_COMUN, 'Admin', 'Prueba', ('administrador',)),
)


class Command(BaseCommand):
    help = 'Prepara una base nueva y archivos locales para E2E; nunca utiliza Supabase.'
    # Primero se valida la configuracion, antes de cualquier acceso a datos.
    requires_system_checks = []

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != 'config.settings_e2e':
            raise CommandError('Usa --settings=config.settings_e2e; no se modificaron datos.')
        directorio = settings.E2E_DIR
        base = settings.DATABASES['default']
        if (base['ENGINE'] != 'django.db.backends.postgresql'
                or base['HOST'] != '127.0.0.1'
                or not (base['NAME'] == 'conecta_e2e' or base['NAME'].startswith('conecta_e2e_'))):
            raise CommandError('Usa una base PostgreSQL local exclusiva del entorno E2E.')
        if settings.STORAGES['default']['BACKEND'] != 'django.core.files.storage.FileSystemStorage':
            raise CommandError('El almacenamiento E2E debe ser local.')
        if any(directorio.iterdir()):
            raise CommandError(
                'La carpeta E2E debe estar vacia. Crea otra para empezar desde cero; '
                'no se borraron ni reiniciaron datos.'
            )

        if connection.introspection.table_names():
            raise CommandError(
                'La base E2E debe estar vacia, sin tablas. Crea otra base de pruebas; '
                'no se borraron ni reiniciaron datos.'
            )

        # No hay flush ni borrado: una repeticion necesita base y carpeta nuevas.
        call_command('migrate', interactive=False, verbosity=0)
        with transaction.atomic():
            manifiesto = self.crear_datos()
        manifiesto['base'] = base['NAME']
        destino = directorio / 'datos-e2e.json'
        destino.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(
            f'Entorno preparado: 10 usuarios, 2 conferencias, 8 articulos y 8 PDF.\n'
            f'Base: {base["NAME"]}\nDatos de referencia: {destino}'
        ))

    def crear_datos(self):
        usuarios = {}
        for alias, correo, password, nombres, apellidos, roles in CUENTAS:
            usuarios[alias] = Usuario.objects.create_user(
                correo, password, nombres=nombres, apellidos=apellidos,
                telefono='3000000000', activo=True,
                **{f'es_{rol}': True for rol in roles},
            )

        ahora = timezone.now()
        hoy = timezone.localdate(ahora)
        conferencias = {}
        for alias, pk, dias_postulacion in (('abierta', 4, 7), ('cerrada', 5, -7)):
            evento = Evento.objects.create(
                pk=pk, nombre=f'Conferencia E2E {alias}', activo=True,
                fecha_inicio=hoy + timedelta(days=40), fecha_fin=hoy + timedelta(days=42),
            )
            for etapa, dias in (
                (FechaLimite.Etapa.POSTULACION, dias_postulacion),
                (FechaLimite.Etapa.REVISION, 14),
                (FechaLimite.Etapa.VERSION_CORREGIDA, 21),
                (FechaLimite.Etapa.VERSION_FINAL, 28),
            ):
                FechaLimite.objects.create(
                    evento=evento, etapa=etapa, fecha=ahora + timedelta(days=dias),
                    creado_por=usuarios['administrador'],
                )
            conferencias[alias] = evento

        # Los IDs explicitos no avanzan la secuencia de PostgreSQL. Sin este
        # ajuste, una conferencia creada despues podria colisionar con el ID 4.
        with connection.cursor() as cursor:
            for sentencia in connection.ops.sequence_reset_sql(no_style(), [Evento]):
                cursor.execute(sentencia)

        # La conferencia 4 mantiene compatible el selector fijo de E2E-11.
        # Los demas IDs se descubren en datos-e2e.json, sin depender de Supabase.
        articulos = {}
        casos = (
            ('consulta', 'articulo2', 'autor_consulta', 'abierta', Articulo.Estado.POSTULADO),
            ('otro_propio', 'estamos melos', 'autor_consulta', 'abierta', Articulo.Estado.POSTULADO),
            ('revision_uno', 'Articulo 1', 'autor_jose', 'cerrada', Articulo.Estado.EN_REVISION),
            ('revision_ia', 'Articulo sobre IA de prueba', 'autor_miguel', 'cerrada', Articulo.Estado.EN_REVISION),
            ('ajeno', 'Prueba Jose', 'autor_jose', 'abierta', Articulo.Estado.POSTULADO),
            ('editable', 'Articulo editable e2e', 'autor_jose', 'abierta', Articulo.Estado.POSTULADO),
            ('no_editable', 'Articulo de prueba para e2e', 'autor_jose', 'cerrada', Articulo.Estado.POSTULADO),
            ('autor_protegido', 'El avance de la IA', 'autor_protegido', 'abierta', Articulo.Estado.POSTULADO),
        )
        for alias, titulo, autor, evento, estado in casos:
            responsable = usuarios[autor]
            articulo = Articulo.objects.create(
                evento=conferencias[evento], autor_responsable=responsable,
                titulo=titulo, resumen='Resumen inicial del articulo de prueba E2E.',
                palabras_clave='pruebas, e2e', linea_tematica=Articulo.LineaTematica.SISTEMAS_SOFTWARE,
                estado=estado, activo=True,
            )
            Autor.objects.create(
                articulo=articulo, nombre=f'{responsable.nombres} {responsable.apellidos}',
                correo=responsable.correo, afiliacion='Universidad del Valle',
            )
            version = VersionArticulo(articulo=articulo, tipo=VersionArticulo.Tipo.INICIAL)
            version.archivo.save('prueba.pdf', ContentFile(PDF_PRUEBA), save=True)
            articulos[alias] = articulo

        coautor = Autor.objects.create(
            articulo=articulos['consulta'], nombre='coautor2ede',
            correo='coautor2ede@prueba.com', afiliacion='univalle',
        )
        return {
            'usuarios': {alias: {'id': usuario.pk, 'correo': usuario.correo, 'roles': usuario.roles}
                         for alias, usuario in usuarios.items()},
            'conferencias': {alias: {'id': evento.pk, 'nombre': evento.nombre}
                            for alias, evento in conferencias.items()},
            'articulos': {alias: {'id': articulo.pk, 'titulo': articulo.titulo}
                         for alias, articulo in articulos.items()},
            'coautor': {'id': coautor.pk, 'correo': coautor.correo},
        }
