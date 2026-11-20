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


    # SCRUM-497: consulta de miembros del comite por linea tematica
    def test_consulta_miembros_activos_del_comite_por_linea_tematica(self):
        experto = Usuario.objects.create_user(
            'experto@correo.com', 'clave12345', nombres='Eva', apellidos='Experta', es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        Usuario.objects.create_user(
            'otra@correo.com', 'clave12345', nombres='Otto', apellidos='OtraLinea', es_comite=True,
            especialidades=[Articulo.LineaTematica.SOFTWARE_PRACTICA],
        )
        Usuario.objects.create_user(
            'inactivo@correo.com', 'clave12345', nombres='Ines', apellidos='Inactiva', es_comite=True, activo=False,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        self.iniciar_sesion(self.administrador, 'administrador')

        respuesta = self.client.get('/api/usuarios/', {'linea_tematica': Articulo.LineaTematica.SISTEMAS_INTELIGENTES})

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual([usuario['id'] for usuario in respuesta.data], [experto.id])

    def test_rechaza_una_linea_tematica_que_no_existe(self):
        self.iniciar_sesion(self.administrador, 'administrador')

        respuesta = self.client.get('/api/usuarios/', {'linea_tematica': 'no_existe'})

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    # SCRUM-498: el comite no puede asignar ni modificar especialidades
    def test_comite_no_puede_modificar_especialidades(self):
        revisor = Usuario.objects.create_user(
            'revisor@correo.com', 'clave12345', nombres='Raul', apellidos='Revisor', es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        comite = Usuario.objects.create_user('comite@correo.com', 'clave12345', nombres='Carla', apellidos='Comite', es_comite=True)
        self.iniciar_sesion(comite, 'comite')

        respuesta = self.client.patch(
            f'/api/usuarios/{revisor.id}/',
            {'especialidades': [Articulo.LineaTematica.SOFTWARE_PRACTICA]},
            format='json',
        )

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        revisor.refresh_from_db()
        self.assertEqual(revisor.especialidades, [Articulo.LineaTematica.SISTEMAS_INTELIGENTES])

    def test_comite_puede_editar_otros_datos_si_no_cambia_especialidades(self):
        revisor = Usuario.objects.create_user(
            'revisor@correo.com', 'clave12345', nombres='Raul', apellidos='Revisor', es_comite=True,
            especialidades=[Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        )
        comite = Usuario.objects.create_user('comite@correo.com', 'clave12345', nombres='Carla', apellidos='Comite', es_comite=True)
        self.iniciar_sesion(comite, 'comite')

        respuesta = self.client.patch(f'/api/usuarios/{revisor.id}/', {'nombres': 'Raul Andres'}, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)

    def test_comite_no_puede_crear_usuarios_con_especialidades(self):
        comite = Usuario.objects.create_user('comite@correo.com', 'clave12345', nombres='Carla', apellidos='Comite', es_comite=True)
        self.iniciar_sesion(comite, 'comite')

        respuesta = self.crear_usuario({
            'es_comite': True,
            'especialidades': [Articulo.LineaTematica.SISTEMAS_INTELIGENTES],
        })

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Usuario.objects.filter(correo='nuevo@correo.com').exists())

