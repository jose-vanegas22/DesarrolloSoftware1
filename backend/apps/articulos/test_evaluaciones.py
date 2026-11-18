from datetime import timedelta
from itertools import product
from unittest.mock import patch
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase
from apps.eventos.models import Evento, FechaLimite
from apps.usuarios.models import Usuario
from .models import Articulo, AsignacionRevision, Autor, Revision, VersionArticulo
from .services import calcular_resultado


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

