from datetime import timedelta
from itertools import product
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.eventos.models import Evento, FechaLimite
from apps.usuarios.models import Usuario
from .models import Articulo, AsignacionRevision, Autor, Revision, VersionArticulo
from .services import calcular_resultado


# HU-13 (SCRUM-24): el autor modifica los datos de su articulo durante las etapas permitidas.
# SCRUM-352: verifica los casos en que la edicion se permite y en los que se bloquea.
class EditarArticuloTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.autor = Usuario.objects.create_user('autor@correo.com', 'clave12345', nombres='Ana', apellidos='Autora', es_autor=True)
        cls.otro_autor = Usuario.objects.create_user('otro@correo.com', 'clave12345', nombres='Otro', apellidos='Autor', es_autor=True)
        cls.comite = Usuario.objects.create_user('comite@correo.com', 'clave12345', nombres='Carlos', apellidos='Comite', es_comite=True)
        cls.administrador = Usuario.objects.create_user('admin@correo.com', 'clave12345', nombres='Ada', apellidos='Admin', es_administrador=True)
        cls.autor_y_comite = Usuario.objects.create_user('ambos@correo.com', 'clave12345', nombres='Beto', apellidos='Ambos', es_autor=True, es_comite=True)

        hoy = timezone.localdate()
        cls.evento_abierto = Evento.objects.create(nombre='Conferencia abierta', fecha_inicio=hoy + timedelta(days=60), fecha_fin=hoy + timedelta(days=64))
        FechaLimite.objects.create(evento=cls.evento_abierto, etapa=FechaLimite.Etapa.POSTULACION, fecha=timezone.now() + timedelta(days=10))

        cls.evento_cerrado = Evento.objects.create(nombre='Conferencia cerrada', fecha_inicio=hoy + timedelta(days=30), fecha_fin=hoy + timedelta(days=34))
        FechaLimite.objects.create(evento=cls.evento_cerrado, etapa=FechaLimite.Etapa.POSTULACION, fecha=timezone.now() - timedelta(days=1))

    def setUp(self):
        self.articulo = self.crear_articulo(self.autor, self.evento_abierto)

    def crear_articulo(self, autor, evento, **extra):
        articulo = Articulo.objects.create(
            evento=evento,
            autor_responsable=autor,
            titulo='Titulo original',
            resumen='Resumen original',
            palabras_clave='uno, dos',
            linea_tematica=Articulo.LineaTematica.SISTEMAS_INTELIGENTES,
            **extra,
        )
        Autor.objects.create(articulo=articulo, nombre=f'{autor.nombres} {autor.apellidos}', afiliacion='Univalle', correo=autor.correo)
        return articulo

    # Inicia sesion con el rol activo indicado, igual que hace el login real
    def iniciar_sesion(self, usuario, rol):
        refresh = RefreshToken.for_user(usuario)
        refresh['rol_activo'] = rol
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def editar(self, articulo, datos):
        return self.client.patch(f'/api/articulos/{articulo.id}/', datos, format='json')

    def assertSinCambios(self, articulo):
        articulo.refresh_from_db()
        self.assertEqual(articulo.titulo, 'Titulo original')
        self.assertEqual(articulo.resumen, 'Resumen original')

    # ---- Edicion permitida ----

    def test_autor_responsable_edita_su_articulo_con_postulacion_abierta(self):
        self.iniciar_sesion(self.autor, 'autor')
        respuesta = self.editar(self.articulo, {
            'titulo': 'Titulo corregido',
            'resumen': 'Resumen corregido',
            'palabras_clave': 'tres, cuatro',
            'linea_tematica': Articulo.LineaTematica.SISTEMAS_SOFTWARE,
        })

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.titulo, 'Titulo corregido')
        self.assertEqual(self.articulo.resumen, 'Resumen corregido')
        self.assertEqual(self.articulo.palabras_clave, 'tres, cuatro')
        self.assertEqual(self.articulo.linea_tematica, Articulo.LineaTematica.SISTEMAS_SOFTWARE)

    def test_patch_parcial_solo_cambia_los_campos_enviados(self):
        self.iniciar_sesion(self.autor, 'autor')
        respuesta = self.editar(self.articulo, {'titulo': 'Solo cambia el titulo'})

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.titulo, 'Solo cambia el titulo')
        self.assertEqual(self.articulo.resumen, 'Resumen original')
        self.assertEqual(self.articulo.palabras_clave, 'uno, dos')

    def test_usuario_con_varios_roles_edita_con_rol_activo_autor(self):
        articulo = self.crear_articulo(self.autor_y_comite, self.evento_abierto)
        self.iniciar_sesion(self.autor_y_comite, 'autor')
        respuesta = self.editar(articulo, {'titulo': 'Titulo corregido'})

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)

    # ---- Edicion bloqueada ----

    def test_otro_autor_no_puede_editar_un_articulo_ajeno(self):
        self.iniciar_sesion(self.otro_autor, 'autor')
        respuesta = self.editar(self.articulo, {'titulo': 'Intento ajeno'})

        # 404 si el articulo ajeno ni siquiera es visible para el autor (como en el detalle), o 403
        self.assertIn(respuesta.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))
        self.assertSinCambios(self.articulo)

    def test_no_se_puede_editar_con_la_postulacion_cerrada(self):
        articulo = self.crear_articulo(self.autor, self.evento_cerrado)
        self.iniciar_sesion(self.autor, 'autor')
        respuesta = self.editar(articulo, {'titulo': 'Fuera de plazo'})

        self.assertIn(respuesta.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN))
        self.assertSinCambios(articulo)

    def test_no_se_puede_editar_si_la_conferencia_no_tiene_fecha_de_postulacion(self):
        evento = Evento.objects.create(nombre='Sin fechas', fecha_inicio=timezone.localdate(), fecha_fin=timezone.localdate())
        articulo = self.crear_articulo(self.autor, evento)
        self.iniciar_sesion(self.autor, 'autor')
        respuesta = self.editar(articulo, {'titulo': 'Sin plazo configurado'})

        self.assertIn(respuesta.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN))
        self.assertSinCambios(articulo)

    def test_comite_no_puede_editar_articulos(self):
        self.iniciar_sesion(self.comite, 'comite')
        respuesta = self.editar(self.articulo, {'titulo': 'Cambio del comite'})

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertSinCambios(self.articulo)

    def test_administrador_no_puede_editar_articulos(self):
        self.iniciar_sesion(self.administrador, 'administrador')
        respuesta = self.editar(self.articulo, {'titulo': 'Cambio del administrador'})

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertSinCambios(self.articulo)

    def test_autor_con_rol_activo_comite_no_puede_editar_su_articulo(self):
        articulo = self.crear_articulo(self.autor_y_comite, self.evento_abierto)
        self.iniciar_sesion(self.autor_y_comite, 'comite')
        respuesta = self.editar(articulo, {'titulo': 'Con el rol equivocado'})

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertSinCambios(articulo)

    def test_sin_sesion_no_se_puede_editar(self):
        respuesta = self.editar(self.articulo, {'titulo': 'Anonimo'})

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertSinCambios(self.articulo)

    def test_articulo_deshabilitado_no_se_puede_editar(self):
        articulo = self.crear_articulo(self.autor, self.evento_abierto, activo=False)
        self.iniciar_sesion(self.autor, 'autor')
        respuesta = self.editar(articulo, {'titulo': 'Deshabilitado'})

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertSinCambios(articulo)

    def test_el_autor_no_puede_cambiar_el_estado(self):
        self.iniciar_sesion(self.autor, 'autor')
        self.editar(self.articulo, {'estado': Articulo.Estado.ACEPTADO})

        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.estado, Articulo.Estado.POSTULADO)

    def test_datos_invalidos_se_rechazan(self):
        self.iniciar_sesion(self.autor, 'autor')
        respuesta = self.editar(self.articulo, {'titulo': '', 'linea_tematica': 'no_existe'})

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('titulo', respuesta.data)
        self.assertIn('linea_tematica', respuesta.data)
        self.assertSinCambios(self.articulo)


# HU-17 y HU-18 (SCRUM-29): registro de evaluaciones y resultado por votos.
class EvaluacionArticuloTests(APITestCase):
    def setUp(self):
        self.autor = Usuario.objects.create_user('autor@example.com', es_autor=True)
        self.revisores = [Usuario.objects.create_user(f'revisor{i}@example.com', es_comite=True) for i in range(3)]
        hoy = timezone.localdate()
        self.evento = Evento.objects.create(nombre='Conferencia', fecha_inicio=hoy, fecha_fin=hoy)
        for etapa, dias in [('postulacion', -1), ('revision', 1)]:
            FechaLimite.objects.create(evento=self.evento, etapa=etapa, fecha=timezone.now() + timedelta(days=dias))
        self.articulo = Articulo.objects.create(
            evento=self.evento, autor_responsable=self.autor, titulo='Artículo de prueba',
            resumen='Resumen', palabras_clave='prueba', linea_tematica='sistemas_software',
        )
        VersionArticulo.objects.create(articulo=self.articulo, tipo='inicial', archivo='prueba.pdf')
        self.asignaciones = [AsignacionRevision.objects.create(articulo=self.articulo, revisor=u) for u in self.revisores]
        self.url = f'/api/articulos/{self.articulo.pk}/evaluacion/'
        self.datos = {'decision': 'aceptar', 'comentarios': 'Contribución clara y bien sustentada.'}
        self.autenticar(self.revisores[0])

    def autenticar(self, usuario, rol='comite'):
        self.client.force_authenticate(user=usuario, token={'rol_activo': rol})

    def test_registra_evaluacion_y_usa_revisor_autenticado(self):
        respuesta = self.client.post(self.url, {**self.datos, 'revisor': self.revisores[1].pk})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(Revision.objects.get().asignacion, self.asignaciones[0])
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.estado, 'en_revision')

    def test_exige_autenticacion(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 401)

    def test_rechaza_comite_sin_asignacion(self):
        usuario = Usuario.objects.create_user('otro@example.com', es_comite=True)
        self.autenticar(usuario)
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 403)
        self.assertFalse(Revision.objects.exists())

    def test_exige_rol_activo_comite(self):
        usuario = self.revisores[0]
        usuario.es_autor = True
        usuario.save()
        self.autenticar(usuario, 'autor')
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 403)

    def test_impide_autoevaluacion_y_coautoria(self):
        for responsable in (True, False):
            with self.subTest(responsable=responsable):
                if responsable:
                    self.articulo.autor_responsable = self.revisores[0]
                    self.articulo.save()
                else:
                    self.articulo.autor_responsable = self.autor
                    self.articulo.save()
                    Autor.objects.create(articulo=self.articulo, nombre='Coautor', afiliacion='Universidad', correo=self.revisores[0].correo.upper())
                self.assertEqual(self.client.post(self.url, self.datos).status_code, 403)

    def test_impide_evaluacion_repetida(self):
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 201)
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 400)
        self.assertEqual(Revision.objects.count(), 1)

    def test_base_de_datos_impide_duplicados(self):
        Revision.objects.create(asignacion=self.asignaciones[0], **self.datos)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Revision.objects.create(asignacion=self.asignaciones[0], **self.datos)

    def test_valida_decision_y_comentarios(self):
        for datos in ({'decision': 'otra', 'comentarios': 'Texto'}, {'decision': 'aceptar', 'comentarios': '   '}, {'decision': 'rechazar'}):
            with self.subTest(datos=datos):
                self.assertEqual(self.client.post(self.url, datos).status_code, 400)
        self.assertFalse(Revision.objects.exists())

    def test_mayoria_y_tercer_voto(self):
        for decision, estado in [('aceptar', 'aceptado'), ('rechazar', 'rechazado')]:
            with self.subTest(decision=decision):
                Revision.objects.all().delete()
                self.articulo.estado = Articulo.Estado.POSTULADO
                self.articulo.save(update_fields=['estado'])
                for i, revisor in enumerate(self.revisores):
                    self.autenticar(revisor)
                    voto = decision if i < 2 else ('rechazar' if decision == 'aceptar' else 'aceptar')
                    self.assertEqual(self.client.post(self.url, {**self.datos, 'decision': voto}).status_code, 201)
                    self.articulo.refresh_from_db()
                    self.assertEqual(self.articulo.estado, 'en_revision' if i < 2 else estado)

    def test_rechaza_fuera_del_plazo_o_sin_fechas(self):
        for etapa, desplazamiento in [('revision', -1), ('postulacion', 1)]:
            with self.subTest(etapa=etapa):
                fecha = self.evento.fechas_limite.get(etapa=etapa)
                original = fecha.fecha
                fecha.fecha = timezone.now() + timedelta(days=desplazamiento)
                fecha.save()
                self.assertEqual(self.client.post(self.url, self.datos).status_code, 400)
                fecha.fecha = original
                fecha.save()
        self.evento.fechas_limite.all().delete()
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 400)

    def test_rechaza_sin_pdf(self):
        self.articulo.versiones.all().delete()
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 400)

    def test_articulo_y_evento_inactivos(self):
        self.evento.activo = False
        self.evento.save()
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 400)
        self.articulo.activo = False
        self.articulo.save()
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 404)

    # SCRUM-370: todas las combinaciones y ordenes de tres votos, incluida unanimidad.
    def test_resultado_de_las_ocho_combinaciones_de_votos(self):
        for votos in product(('aceptar', 'rechazar'), repeat=3):
            with self.subTest(votos=votos):
                Revision.objects.all().delete()
                self.articulo.estado = Articulo.Estado.POSTULADO
                self.articulo.save(update_fields=['estado'])
                for indice, voto in enumerate(votos):
                    self.autenticar(self.revisores[indice])
                    respuesta = self.client.post(self.url, {**self.datos, 'decision': voto})
                    self.assertEqual(respuesta.status_code, 201, respuesta.data)
                    self.articulo.refresh_from_db()
                    esperado = 'en_revision' if indice < 2 else (
                        'aceptado' if votos.count('aceptar') >= 2 else 'rechazado'
                    )
                    self.assertEqual(self.articulo.estado, esperado)
                    self.assertEqual(Revision.objects.filter(asignacion__articulo=self.articulo).count(), indice + 1)

    def test_calculo_sin_evaluaciones_no_decide(self):
        self.articulo.estado = Articulo.Estado.EN_REVISION
        self.articulo.save(update_fields=['estado'])
        self.assertIsNone(calcular_resultado(self.articulo))
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.estado, Articulo.Estado.EN_REVISION)

    def test_recalculo_no_modifica_resultado_final(self):
        for revisor in self.revisores:
            self.autenticar(revisor)
            self.assertEqual(self.client.post(self.url, self.datos).status_code, 201)
        # El servicio debe leer el estado persistido, aunque reciba una instancia desactualizada.
        self.articulo.estado = Articulo.Estado.EN_REVISION
        self.assertIsNone(calcular_resultado(self.articulo))
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.estado, Articulo.Estado.ACEPTADO)

    def test_fallo_del_calculo_revierte_la_tercera_evaluacion(self):
        for revisor in self.revisores[:2]:
            self.autenticar(revisor)
            self.assertEqual(self.client.post(self.url, self.datos).status_code, 201)
        self.autenticar(self.revisores[2])
        with patch('apps.articulos.services.calcular_resultado', side_effect=RuntimeError('Fallo de prueba')):
            with self.assertRaises(RuntimeError):
                self.client.post(self.url, self.datos)
        self.assertEqual(Revision.objects.count(), 2)
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.estado, Articulo.Estado.EN_REVISION)
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 201)
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.estado, Articulo.Estado.ACEPTADO)

    def test_no_se_registra_un_cuarto_voto(self):
        for revisor in self.revisores:
            self.autenticar(revisor)
            self.assertEqual(self.client.post(self.url, self.datos).status_code, 201)
        extra = Usuario.objects.create_user('extra@example.com', es_comite=True)
        AsignacionRevision.objects.create(articulo=self.articulo, revisor=extra)
        self.autenticar(extra)
        self.assertEqual(self.client.post(self.url, {**self.datos, 'decision': 'rechazar'}).status_code, 400)
        self.assertEqual(Revision.objects.count(), 3)
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.estado, Articulo.Estado.ACEPTADO)

    def test_no_cuenta_votos_de_otro_articulo(self):
        otro = Articulo.objects.create(
            evento=self.evento, autor_responsable=self.autor, titulo='Otro artículo',
            resumen='Resumen', palabras_clave='prueba', linea_tematica='sistemas_software',
        )
        for revisor in self.revisores:
            asignacion = AsignacionRevision.objects.create(articulo=otro, revisor=revisor)
            Revision.objects.create(asignacion=asignacion, **self.datos)
        self.assertEqual(self.client.post(self.url, self.datos).status_code, 201)
        self.articulo.refresh_from_db()
        self.assertEqual(self.articulo.estado, Articulo.Estado.EN_REVISION)
