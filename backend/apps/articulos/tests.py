from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.eventos.models import Evento, FechaLimite
from apps.usuarios.models import Usuario
from .models import Articulo, Autor


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
