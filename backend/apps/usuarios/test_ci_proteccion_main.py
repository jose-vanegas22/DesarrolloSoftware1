"""Ensayo temporal de SCRUM-616: no integrar este archivo en main."""

from django.test import SimpleTestCase


class ProteccionMainCITests(SimpleTestCase):
    def test_check_fallido_debe_bloquear_merge(self):
        self.fail(
            'SCRUM-616: fallo deliberado para comprobar el bloqueo del merge. '
            'Verificar la proteccion en el PR; esta prueba solo provoca el fallo.'
        )
