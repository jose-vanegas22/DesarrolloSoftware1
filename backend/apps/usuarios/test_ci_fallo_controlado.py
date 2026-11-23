"""Ensayo temporal de SCRUM-599: no integrar este archivo en main."""

from django.test import SimpleTestCase


class FalloControladoCITests(SimpleTestCase):
    def test_ci_detecta_una_prueba_fallida(self):
        self.fail('SCRUM-599: fallo deliberado para verificar que CI detecta errores.')
