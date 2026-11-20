from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.articulos.models import Articulo
from .models import Usuario


# SCRUM-291: la experiencia del revisor se guarda como lineas tematicas y solo aplica al comite.
class EspecialidadesUsuarioTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.administrador = Usuario.objects.create_user(
            'admin@correo.com', 'clave12345',
            nombres='Ada', apellidos='Admin', es_administrador=True,
        )

    def iniciar_sesion(self, usuario, rol):
        refresh = RefreshToken.for_user(usuario)
        refresh['rol_activo'] = rol
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def crear_usuario(self, datos):
        base = {
            'correo': 'nuevo@correo.com',
            'password': 'ClaveSegura-2026!',
            'nombres': 'Nuevo',
            'apellidos': 'Usuario',
            'telefono': '3001234567',
        }
        return self.client.post('/api/usuarios/', {**base, **datos}, format='json')

    def test_admin_crea_miembro_del_comite_con_especialidades(self):
        self.iniciar_sesion(self.administrador, 'administrador')

        respuesta = self.crear_usuario({
            'correo': 'comite@correo.com',
            'es_comite': True,
            'especialidades': [
                Articulo.LineaTematica.SISTEMAS_INTELIGENTES,
                Articulo.LineaTematica.SOFTWARE_PRACTICA,
            ],
        })

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        usuario = Usuario.objects.get(correo='comite@correo.com')
        self.assertEqual(
            usuario.especialidades,
            [
                Articulo.LineaTematica.SISTEMAS_INTELIGENTES,
                Articulo.LineaTematica.SOFTWARE_PRACTICA,
            ],
        )

    def test_no_permite_especialidades_en_un_usuario_que_no_es_comite(self):
        self.iniciar_sesion(self.administrador, 'administrador')

        respuesta = self.crear_usuario({
            'es_autor': True,
            'especialidades': [Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        })

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('especialidades', respuesta.data)
        self.assertFalse(Usuario.objects.filter(correo='nuevo@correo.com').exists())

    def test_no_permite_especialidades_que_no_son_lineas_tematicas(self):
        self.iniciar_sesion(self.administrador, 'administrador')

        respuesta = self.crear_usuario({
            'es_comite': True,
            'especialidades': ['no_existe'],
        })

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('especialidades', respuesta.data)
        self.assertFalse(Usuario.objects.filter(correo='nuevo@correo.com').exists())

    def test_no_permite_quitar_el_rol_de_comite_mientras_conserve_especialidades(self):
        comite = Usuario.objects.create_user(
            'comite@correo.com', 'clave12345',
            nombres='Carla', apellidos='Comite', es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        self.iniciar_sesion(self.administrador, 'administrador')

        respuesta = self.client.patch(
            f'/api/usuarios/{comite.id}/',
            {'es_comite': False, 'es_autor': True},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('especialidades', respuesta.data)
        comite.refresh_from_db()
        self.assertTrue(comite.es_comite)
        self.assertEqual(comite.especialidades, [Articulo.LineaTematica.SISTEMAS_INTELIGENTES])
