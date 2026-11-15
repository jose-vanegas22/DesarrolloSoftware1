from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.eventos.models import Evento, FechaLimite
from apps.usuarios.models import Usuario
from .models import Articulo, AsignacionRevision, Autor, Revision


# HU-16 (SCRUM-27): asignar tres revisores a un articulo despues de cerrar la postulacion.
class AsignarRevisoresTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        hoy = timezone.localdate()
        cls.evento = Evento.objects.create(
            nombre='Conferencia con postulacion cerrada',
            fecha_inicio=hoy + timedelta(days=30),
            fecha_fin=hoy + timedelta(days=34),
        )
        FechaLimite.objects.create(
            evento=cls.evento,
            etapa=FechaLimite.Etapa.POSTULACION,
            fecha=timezone.now() - timedelta(days=1),
        )

        cls.autor = Usuario.objects.create_user(
            'autor@correo.com', 'clave12345',
            nombres='Ana', apellidos='Autora', es_autor=True, es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        cls.coautor = Usuario.objects.create_user(
            'coautor@correo.com', 'clave12345',
            nombres='Carla', apellidos='Coautora', es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        cls.comite_1 = Usuario.objects.create_user(
            'comite1@correo.com', 'clave12345',
            nombres='Carlos', apellidos='Comite', es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        cls.comite_2 = Usuario.objects.create_user(
            'comite2@correo.com', 'clave12345',
            nombres='Diana', apellidos='Comite', es_comite=True,
            especialidades=[
                Articulo.LineaTematica.SISTEMAS_INTELIGENTES,
                Articulo.LineaTematica.SISTEMAS_SOFTWARE,
            ],
        )
        cls.comite_3 = Usuario.objects.create_user(
            'comite3@correo.com', 'clave12345',
            nombres='Elena', apellidos='Comite', es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        cls.comite_otra_linea = Usuario.objects.create_user(
            'otra@correo.com', 'clave12345',
            nombres='Felipe', apellidos='OtraLinea', es_comite=True,
            especialidades=[Articulo.LineaTematica.SOFTWARE_PRACTICA],
        )
        cls.no_comite = Usuario.objects.create_user(
            'nocomite@correo.com', 'clave12345',
            nombres='Gloria', apellidos='Autora', es_autor=True,
        )
        cls.administrador = Usuario.objects.create_user(
            'admin@correo.com', 'clave12345',
            nombres='Hugo', apellidos='Admin', es_administrador=True,
        )

        cls.articulo = cls.crear_articulo(cls.autor)
        Autor.objects.create(
            articulo=cls.articulo,
            nombre=f'{cls.coautor.nombres} {cls.coautor.apellidos}',
            afiliacion='Univalle',
            correo=cls.coautor.correo,
        )

    @classmethod
    def crear_articulo(cls, autor, evento=None, linea_tematica=None):
        articulo = Articulo.objects.create(
            evento=evento or cls.evento,
            autor_responsable=autor,
            titulo='Articulo de prueba',
            resumen='Resumen de prueba',
            palabras_clave='prueba, revisores',
            linea_tematica=linea_tematica or Articulo.LineaTematica.SISTEMAS_INTELIGENTES,
        )
        Autor.objects.create(
            articulo=articulo,
            nombre=f'{autor.nombres} {autor.apellidos}',
            afiliacion='Univalle',
            correo=autor.correo,
        )
        return articulo

    def iniciar_sesion(self, usuario, rol):
        refresh = RefreshToken.for_user(usuario)
        refresh['rol_activo'] = rol
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def asignar(self, revisores, articulo=None):
        articulo = articulo or self.articulo
        return self.client.post(
            f'/api/articulos/{articulo.id}/revisores/',
            {'revisores': [revisor.id for revisor in revisores]},
            format='json',
        )

    # ---- Asignacion valida ----

    def test_asignacion_valida_guarda_tres_revisores(self):
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.comite_1, self.comite_2, self.comite_3])

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(len(respuesta.data), 3)

        asignaciones = AsignacionRevision.objects.filter(articulo=self.articulo)
        self.assertEqual(asignaciones.count(), 3)
        self.assertEqual(
            set(asignaciones.values_list('revisor_id', flat=True)),
            {self.comite_1.id, self.comite_2.id, self.comite_3.id},
        )

    def test_consulta_devuelve_las_asignaciones_guardadas(self):
        self.iniciar_sesion(self.comite_1, 'comite')
        self.asignar([self.comite_1, self.comite_2, self.comite_3])

        respuesta = self.client.get(f'/api/articulos/{self.articulo.id}/revisores/')

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(
            {asignacion['revisor'] for asignacion in respuesta.data},
            {self.comite_1.id, self.comite_2.id, self.comite_3.id},
        )

    def test_reenviar_los_mismos_revisores_no_duplica_la_asignacion(self):
        self.iniciar_sesion(self.comite_1, 'comite')

        primera = self.asignar([self.comite_1, self.comite_2, self.comite_3])
        segunda = self.asignar([self.comite_1, self.comite_2, self.comite_3])

        self.assertEqual(primera.status_code, status.HTTP_201_CREATED, primera.data)
        self.assertEqual(segunda.status_code, status.HTTP_201_CREATED, segunda.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 3)

    # ---- Reglas de negocio ----

    def test_no_permite_revisores_repetidos(self):
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.comite_1, self.comite_1, self.comite_2])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_exige_exactamente_tres_revisores(self):
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.comite_1, self.comite_2])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_no_permite_revisores_fuera_del_comite(self):
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.comite_1, self.comite_2, self.no_comite])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_no_permite_asignar_antes_de_la_fecha_limite(self):
        evento_abierto = Evento.objects.create(
            nombre='Conferencia con postulacion abierta',
            fecha_inicio=timezone.localdate() + timedelta(days=30),
            fecha_fin=timezone.localdate() + timedelta(days=34),
        )
        FechaLimite.objects.create(
            evento=evento_abierto,
            etapa=FechaLimite.Etapa.POSTULACION,
            fecha=timezone.now() + timedelta(days=10),
        )
        articulo_abierto = self.crear_articulo(self.autor, evento=evento_abierto)
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar(
            [self.comite_1, self.comite_2, self.comite_3],
            articulo=articulo_abierto,
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=articulo_abierto).count(), 0)

    def test_no_permite_asignar_si_el_evento_no_tiene_fecha_de_postulacion(self):
        evento_sin_fecha = Evento.objects.create(
            nombre='Conferencia sin fecha',
            fecha_inicio=timezone.localdate() + timedelta(days=30),
            fecha_fin=timezone.localdate() + timedelta(days=34),
        )
        articulo_sin_fecha = self.crear_articulo(self.autor, evento=evento_sin_fecha)
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar(
            [self.comite_1, self.comite_2, self.comite_3],
            articulo=articulo_sin_fecha,
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=articulo_sin_fecha).count(), 0)

    def test_no_permite_asignar_al_autor_responsable(self):
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.autor, self.comite_1, self.comite_2])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_no_permite_asignar_a_un_coautor(self):
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.coautor, self.comite_1, self.comite_2])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_no_permite_revisores_sin_la_linea_tematica_del_articulo(self):
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.comite_1, self.comite_2, self.comite_otra_linea])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_permite_asignar_si_el_revisor_tiene_dos_articulos_previos(self):
        for _ in range(2):
            otro_articulo = self.crear_articulo(self.autor)
            AsignacionRevision.objects.create(
                articulo=otro_articulo,
                revisor=self.comite_1,
            )
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.comite_1, self.comite_2, self.comite_3])

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 3)

    def test_no_permite_mas_de_tres_articulos_por_revisor(self):
        for _ in range(3):
            otro_articulo = self.crear_articulo(self.autor)
            AsignacionRevision.objects.create(
                articulo=otro_articulo,
                revisor=self.comite_1,
            )
        self.iniciar_sesion(self.comite_1, 'comite')

        respuesta = self.asignar([self.comite_1, self.comite_2, self.comite_3])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revisores', respuesta.data)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_no_permite_quitar_a_un_revisor_que_ya_evaluo(self):
        self.iniciar_sesion(self.comite_1, 'comite')
        self.asignar([self.comite_1, self.comite_2, self.comite_3])
        asignacion = AsignacionRevision.objects.get(articulo=self.articulo, revisor=self.comite_1)
        Revision.objects.create(
            asignacion=asignacion,
            decision=Revision.Decision.ACEPTAR,
            comentarios='Trabajo aprobado.',
        )
        comite_4 = Usuario.objects.create_user(
            'comite4@correo.com', 'clave12345',
            nombres='Irene', apellidos='Comite', es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )

        respuesta = self.asignar([self.comite_2, self.comite_3, comite_4])

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST, respuesta.data)
        self.assertIn('detail', respuesta.data)
        self.assertTrue(
            AsignacionRevision.objects.filter(articulo=self.articulo, revisor=self.comite_1).exists()
        )

    # ---- Permisos ----

    def test_autor_no_puede_asignar_revisores(self):
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.asignar([self.comite_1, self.comite_2, self.comite_3])

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_administrador_no_puede_asignar_revisores(self):
        self.iniciar_sesion(self.administrador, 'administrador')

        respuesta = self.asignar([self.comite_1, self.comite_2, self.comite_3])

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(AsignacionRevision.objects.filter(articulo=self.articulo).count(), 0)

    def test_sin_sesion_no_puede_asignar_revisores(self):
        respuesta = self.asignar([self.comite_1, self.comite_2, self.comite_3])

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_autor_no_puede_consultar_los_revisores(self):
        self.iniciar_sesion(self.comite_1, 'comite')
        self.asignar([self.comite_1, self.comite_2, self.comite_3])
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.client.get(f'/api/articulos/{self.articulo.id}/revisores/')

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
