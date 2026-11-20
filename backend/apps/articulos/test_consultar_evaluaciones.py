from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.eventos.models import Evento, FechaLimite
from apps.usuarios.models import Usuario
from .models import Articulo, AsignacionRevision, Autor, Revision


# HU-70 (SCRUM-394): el autor consulta las evaluaciones de su propio articulo.
# SCRUM-397: verificar el acceso a las evaluaciones.
class ConsultarEvaluacionesTests(APITestCase):

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
            nombres='Ana', apellidos='Autora', es_autor=True,
        )
        cls.otro_autor = Usuario.objects.create_user(
            'otro@correo.com', 'clave12345',
            nombres='Bruno', apellidos='Autor', es_autor=True,
        )
        cls.revisor_1 = Usuario.objects.create_user(
            'revisor1@correo.com', 'clave12345',
            nombres='Carlos', apellidos='Revisor', es_comite=True,
        )
        cls.revisor_2 = Usuario.objects.create_user(
            'revisor2@correo.com', 'clave12345',
            nombres='Diana', apellidos='Revisora', es_comite=True,
        )

        cls.articulo = cls.crear_articulo(cls.autor)
        cls.articulo_sin_evaluaciones = cls.crear_articulo(cls.autor)
        cls.articulo_ajeno = cls.crear_articulo(cls.otro_autor)

        cls.evaluar(cls.articulo, cls.revisor_1, Revision.Decision.ACEPTAR, 'Buen trabajo, corregir la introduccion.')
        cls.evaluar(cls.articulo, cls.revisor_2, Revision.Decision.RECHAZAR, 'Falta sustentar la metodologia.')
        cls.evaluar(cls.articulo_ajeno, cls.revisor_1, Revision.Decision.ACEPTAR, 'Evaluacion de otro articulo.')

    @classmethod
    def crear_articulo(cls, autor):
        articulo = Articulo.objects.create(
            evento=cls.evento,
            autor_responsable=autor,
            titulo='Articulo de prueba',
            resumen='Resumen de prueba',
            palabras_clave='prueba, evaluaciones',
            linea_tematica=Articulo.LineaTematica.SISTEMAS_INTELIGENTES,
            estado=Articulo.Estado.EN_REVISION,
        )
        Autor.objects.create(
            articulo=articulo,
            nombre=f'{autor.nombres} {autor.apellidos}',
            afiliacion='Univalle',
            correo=autor.correo,
        )
        return articulo

    @classmethod
    def evaluar(cls, articulo, revisor, decision, comentarios):
        asignacion = AsignacionRevision.objects.create(articulo=articulo, revisor=revisor)
        return Revision.objects.create(asignacion=asignacion, decision=decision, comentarios=comentarios)

    def iniciar_sesion(self, usuario, rol):
        refresh = RefreshToken.for_user(usuario)
        refresh['rol_activo'] = rol
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def consultar(self, articulo_id):
        return self.client.get(f'/api/articulos/{articulo_id}/evaluaciones/')

    # ---- Acceso permitido ----

    def test_autor_consulta_las_evaluaciones_de_su_articulo(self):
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.consultar(self.articulo.id)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(len(respuesta.data), 2)
        self.assertEqual(
            {evaluacion['decision'] for evaluacion in respuesta.data},
            {Revision.Decision.ACEPTAR, Revision.Decision.RECHAZAR},
        )
        self.assertIn('Falta sustentar la metodologia.', [e['comentarios'] for e in respuesta.data])

    def test_solo_devuelve_las_evaluaciones_de_ese_articulo(self):
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.consultar(self.articulo.id)

        comentarios = [evaluacion['comentarios'] for evaluacion in respuesta.data]
        self.assertNotIn('Evaluacion de otro articulo.', comentarios)

    def test_articulo_sin_evaluaciones_devuelve_lista_vacia(self):
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.consultar(self.articulo_sin_evaluaciones.id)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data, [])

    def test_no_expone_la_identidad_del_revisor(self):
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.consultar(self.articulo.id)

        for evaluacion in respuesta.data:
            self.assertEqual(set(evaluacion.keys()), {'id', 'decision', 'comentarios', 'creado'})
            self.assertNotIn(self.revisor_1.correo, str(evaluacion))
            self.assertNotIn(self.revisor_2.correo, str(evaluacion))

    # ---- Acceso denegado ----

    def test_autor_no_puede_consultar_un_articulo_ajeno(self):
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.consultar(self.articulo_ajeno.id)

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_articulo_inexistente_responde_404(self):
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.consultar(999999)

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_articulo_deshabilitado_responde_404(self):
        Articulo.objects.filter(pk=self.articulo.pk).update(activo=False)
        self.iniciar_sesion(self.autor, 'autor')

        respuesta = self.consultar(self.articulo.id)

        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_rol_comite_no_puede_consultar_evaluaciones_del_autor(self):
        self.iniciar_sesion(self.revisor_1, 'comite')

        respuesta = self.consultar(self.articulo.id)

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_sin_sesion_responde_401(self):
        respuesta = self.consultar(self.articulo.id)

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)