from datetime import timedelta
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase
from apps.eventos.models import Evento, FechaLimite
from apps.usuarios.models import Usuario
from .models import Articulo, AsignacionRevision, Autor, Revision, VersionArticulo


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
                for i, revisor in enumerate(self.revisores):
                    self.autenticar(revisor)
                    voto = decision if i < 2 else ('rechazar' if decision == 'aceptar' else 'aceptar')
                    self.assertEqual(self.client.post(self.url, {**self.datos, 'decision': voto}).status_code, 201)
                    self.articulo.refresh_from_db()
                    self.assertEqual(self.articulo.estado, 'en_revision' if i == 0 else estado)

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

    def test_detalle_muestra_pdf_y_solo_revision_propia(self):
        url = f'/api/articulos/{self.articulo.pk}/'
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.data['evaluacion']['puede_evaluar'])
        self.assertTrue(respuesta.data['pdf_url'].endswith('prueba.pdf'))
        self.client.post(self.url, self.datos)
        respuesta = self.client.get(url)
        self.assertFalse(respuesta.data['evaluacion']['puede_evaluar'])
        self.assertEqual(respuesta.data['evaluacion']['revision']['decision'], 'aceptar')
        self.autenticar(self.revisores[1])
        self.assertIsNone(self.client.get(url).data['evaluacion']['revision'])

    def test_detalle_y_lista_del_autor_siguen_disponibles(self):
        self.autenticar(self.autor, 'autor')
        respuesta = self.client.get(f'/api/articulos/{self.articulo.pk}/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.data['evaluacion']['puede_evaluar'])
        self.assertEqual(len(self.client.get('/api/articulos/').data), 1)
