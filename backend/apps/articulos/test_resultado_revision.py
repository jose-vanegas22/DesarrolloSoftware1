from django.test import TestCase

from .models import Articulo
from .services import resultado_por_votos


class ResultadoPorVotosTests(SimpleTestCase):
    # Cada metodo que empieza con test_ lo ejecuta Django por separado

    def test_tres_aceptan_da_aceptado(self):
        resultado = resultado_por_votos(aceptan=3, rechazan=0, total=3)
        self.assertEqual(resultado, Articulo.Estado.ACEPTADO)

    def test_dos_aceptan_y_uno_rechaza_da_aceptado(self):
        resultado = resultado_por_votos(aceptan=2, rechazan=1, total=3)
        self.assertEqual(resultado, Articulo.Estado.ACEPTADO)

    def test_uno_acepta_y_dos_rechazan_da_rechazado(self):
        resultado = resultado_por_votos(aceptan=1, rechazan=2, total=3)
        self.assertEqual(resultado, Articulo.Estado.RECHAZADO)

    def test_tres_rechazan_da_rechazado(self):
        resultado = resultado_por_votos(aceptan=0, rechazan=3, total=3)
        self.assertEqual(resultado, Articulo.Estado.RECHAZADO)

    def test_sin_las_tres_evaluaciones_no_decide(self):
        # Aunque los dos votos sean de aceptacion, faltan evaluaciones: no se calcula
        resultado = resultado_por_votos(aceptan=2, rechazan=0, total=2)
        self.assertIsNone(resultado)

    def test_sin_evaluaciones_no_decide(self):
        resultado = resultado_por_votos(aceptan=0, rechazan=0, total=0)
        self.assertIsNone(resultado)