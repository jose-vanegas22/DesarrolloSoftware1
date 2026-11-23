from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .models import Usuario
from .permissions import es_administrador, es_gestor, obtener_rol_activo


# SCRUM-602 / HU-07: permisos del rol activo, sin base de datos ni red.
class PermisosAccesoUnitariosTests(SimpleTestCase):
    def peticion(self, auth, **roles):
        usuario = SimpleNamespace(
            **{'es_autor': False, 'es_comite': False, 'es_administrador': False, **roles},
        )
        return SimpleNamespace(auth=auth, user=usuario)

    def test_reconoce_solo_el_rol_activo_asignado(self):
        for rol in ('autor', 'comite', 'administrador'):
            with self.subTest(rol=rol):
                request = self.peticion(
                    {'rol_activo': rol}, es_autor=True, es_comite=True, es_administrador=True,
                )
                self.assertEqual(obtener_rol_activo(request), rol)

    def test_rechaza_rol_ausente_desconocido_o_no_asignado(self):
        for auth in (None, {}, {'rol_activo': None}, {'rol_activo': 'inexistente'},
                     {'rol_activo': 'comite'}, {'rol_activo': 'administrador'}):
            with self.subTest(auth=auth):
                request = self.peticion(auth, es_autor=True)
                self.assertIsNone(obtener_rol_activo(request))

    def test_gestor_exige_rol_activo_administrador_o_comite_asignado(self):
        casos = (
            ('administrador', True, True), ('comite', True, True),
            ('autor', True, False), ('administrador', False, False),
            ('comite', False, False), (None, False, False), ('inexistente', False, False),
        )
        for rol, asignado, esperado in casos:
            with self.subTest(rol=rol, asignado=asignado):
                roles = {f'es_{rol}': True} if asignado else {}
                request = self.peticion({'rol_activo': rol}, **roles)
                self.assertEqual(es_gestor(request), esperado)
        request = self.peticion(
            {'rol_activo': 'autor'}, es_autor=True, es_comite=True, es_administrador=True,
        )
        self.assertFalse(es_gestor(request))

    def test_administrador_exige_rol_activo_administrador_asignado(self):
        for rol, esperado in (('administrador', True), ('comite', False),
                              ('autor', False), (None, False), ('inexistente', False)):
            with self.subTest(rol=rol):
                request = self.peticion(
                    {'rol_activo': rol}, es_administrador=True, es_comite=True, es_autor=True,
                )
                self.assertEqual(es_administrador(request), esperado)
        request = self.peticion({'rol_activo': 'administrador'}, es_autor=True)
        self.assertFalse(es_administrador(request))


# SCRUM-603 / HU-03 y HU-43; SCRUM-604 / HU-07.
# Integracion: rutas, serializers, autenticacion, JWT y base de datos reales de prueba.
class AccesoIntegracionTests(APITestCase):
    PASSWORD = 'Acceso-Pruebas-2026!'
    CAPTCHA = 'captcha-controlado-para-pruebas'
    LOGIN_URL = '/api/token/'
    ROL_URL = '/api/usuarios/seleccionar-rol/'

    @classmethod
    def setUpTestData(cls):
        cls.autor = Usuario.objects.create_user(
            'autor@acceso.test', cls.PASSWORD,
            nombres='Ana', apellidos='Autora', es_autor=True,
        )
        cls.multirrol = Usuario.objects.create_user(
            'multirrol@acceso.test', cls.PASSWORD,
            nombres='Camilo', apellidos='Comite', es_autor=True, es_comite=True,
        )

    def setUp(self):
        # Se sustituye la consulta externa, no la autenticacion ni la emision de JWT.
        captcha = patch('apps.usuarios.serializers.verificar_captcha', return_value=True)
        self.verificar_captcha = captcha.start()
        self.addCleanup(captcha.stop)
        self.ahora = timezone.now()

    def login(self, usuario, password=None):
        return self.client.post(self.LOGIN_URL, {
            'correo': usuario.correo,
            'password': self.PASSWORD if password is None else password,
            'captcha': self.CAPTCHA,
        }, format='json')

    def assertSinTokens(self, respuesta):
        self.assertNotIn('access', respuesta.data)
        self.assertNotIn('refresh', respuesta.data)

    def assertSesionValida(self, respuesta, usuario, rol, roles):
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(respuesta.data['rol_activo'], rol)
        self.assertCountEqual(respuesta.data['roles'], roles)
        # Estas clases verifican firma, vigencia y tipo; no solo decodifican JSON.
        access = AccessToken(respuesta.data['access'])
        refresh = RefreshToken(respuesta.data['refresh'])
        for token in (access, refresh):
            self.assertEqual(str(token['user_id']), str(usuario.pk))
            self.assertEqual(token['rol_activo'], rol)

    def test_login_con_un_rol_emite_tokens_con_ese_rol(self):
        for rol in ('autor', 'comite', 'administrador'):
            with self.subTest(rol=rol):
                usuario = Usuario.objects.create_user(
                    f'{rol}.unico@acceso.test', self.PASSWORD,
                    nombres='Usuario', apellidos='Un rol', **{f'es_{rol}': True},
                )
                respuesta = self.login(usuario)
                self.assertSesionValida(respuesta, usuario, rol, [rol])
                self.verificar_captcha.assert_called_with(self.CAPTCHA, '127.0.0.1')

    def test_login_multirrol_emite_tokens_sin_rol_activo(self):
        respuesta = self.login(self.multirrol)
        self.assertSesionValida(respuesta, self.multirrol, None, ['autor', 'comite'])

    def test_captcha_invalido_rechaza_login_sin_alterar_intentos(self):
        self.autor.intentos_fallidos = 2
        self.autor.save(update_fields=['intentos_fallidos'])
        self.verificar_captcha.return_value = False

        respuesta = self.login(self.autor)

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('captcha', respuesta.data)
        self.assertSinTokens(respuesta)
        self.verificar_captcha.assert_called_once_with(self.CAPTCHA, '127.0.0.1')
        self.autor.refresh_from_db()
        self.assertEqual(self.autor.intentos_fallidos, 2)
        self.assertIsNone(self.autor.bloqueado_hasta)

    def test_quinto_fallo_activa_bloqueo_de_quince_minutos(self):
        with patch('apps.usuarios.serializers.timezone.now', return_value=self.ahora):
            for intento in range(1, 6):
                with self.subTest(intento=intento):
                    respuesta = self.login(self.autor, password='password-incorrecta')
                    self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
                    self.assertSinTokens(respuesta)
                    self.autor.refresh_from_db()
                    if intento < 5:
                        self.assertEqual(self.autor.intentos_fallidos, intento)
                        self.assertIsNone(self.autor.bloqueado_hasta)
                    else:
                        self.assertEqual(self.autor.intentos_fallidos, 0)
                        self.assertEqual(
                            self.autor.bloqueado_hasta, self.ahora + timedelta(minutes=15),
                        )

    def test_cuenta_bloqueada_rechaza_password_correcta(self):
        limite = self.ahora + timedelta(minutes=15)
        self.autor.bloqueado_hasta = limite
        self.autor.save(update_fields=['bloqueado_hasta'])

        with patch('apps.usuarios.serializers.timezone.now', return_value=self.ahora):
            respuesta = self.login(self.autor)

        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Cuenta bloqueada', str(respuesta.data['detail']))
        self.assertSinTokens(respuesta)
        self.autor.refresh_from_db()
        self.assertEqual(self.autor.bloqueado_hasta, limite)
        self.assertEqual(self.autor.intentos_fallidos, 0)

    def test_login_respeta_el_limite_del_bloqueo_y_limpia_su_estado(self):
        limite = self.ahora + timedelta(minutes=15)
        for segundos in (-1, 0, 1):
            with self.subTest(segundos_desde_vencimiento=segundos):
                # Cada variante empieza con una cuenta bloqueada, sin depender de la anterior.
                self.autor.bloqueado_hasta = limite
                self.autor.intentos_fallidos = 0
                self.autor.save(update_fields=['bloqueado_hasta', 'intentos_fallidos'])
                instante = limite + timedelta(seconds=segundos)
                with patch('apps.usuarios.serializers.timezone.now', return_value=instante):
                    respuesta = self.login(self.autor)
                self.autor.refresh_from_db()
                if segundos < 0:
                    self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
                    self.assertSinTokens(respuesta)
                    self.assertEqual(self.autor.bloqueado_hasta, limite)
                else:
                    self.assertSesionValida(respuesta, self.autor, 'autor', ['autor'])
                    self.assertIsNone(self.autor.bloqueado_hasta)
                self.assertEqual(self.autor.intentos_fallidos, 0)

    def test_login_correcto_reinicia_intentos_antes_del_bloqueo(self):
        for _ in range(2):
            respuesta = self.login(self.autor, password='password-incorrecta')
            self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

        respuesta = self.login(self.autor)

        self.assertSesionValida(respuesta, self.autor, 'autor', ['autor'])
        self.autor.refresh_from_db()
        self.assertEqual(self.autor.intentos_fallidos, 0)
        self.assertIsNone(self.autor.bloqueado_hasta)
        respuesta = self.login(self.autor, password='password-incorrecta')
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.autor.refresh_from_db()
        self.assertEqual(self.autor.intentos_fallidos, 1)
        self.assertIsNone(self.autor.bloqueado_hasta)

    def test_seleccion_de_rol_asignado_emite_nuevos_tokens(self):
        sesion = self.login(self.multirrol)
        self.assertSesionValida(sesion, self.multirrol, None, ['autor', 'comite'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {sesion.data["access"]}')

        for rol in ('autor', 'comite'):
            with self.subTest(rol=rol):
                respuesta = self.client.post(self.ROL_URL, {'rol': rol}, format='json')
                self.assertSesionValida(respuesta, self.multirrol, rol, ['autor', 'comite'])
                for tipo in ('access', 'refresh'):
                    self.assertNotEqual(respuesta.data[tipo], sesion.data[tipo])

    def test_seleccion_de_rol_no_asignado_rechaza_peticion_directa(self):
        sesion = self.login(self.multirrol)
        self.assertSesionValida(sesion, self.multirrol, None, ['autor', 'comite'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {sesion.data["access"]}')

        respuesta = self.client.post(self.ROL_URL, {'rol': 'administrador'}, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rol', respuesta.data)
        self.assertSinTokens(respuesta)
        self.multirrol.refresh_from_db()
        self.assertFalse(self.multirrol.es_administrador)
