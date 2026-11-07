from django.db import models
from django.conf import settings
from django.utils import timezone


class Evento(models.Model):
    nombre = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    agenda_publicada = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_inicio', 'nombre']

    def __str__(self):
        return self.nombre

    # Nos permite saber si la postulación de artículos para este evento está abierta, es decir, si el evento está activo y la fecha límite de postulación no ha pasado.
    @property
    def postulacion_abierta(self) -> bool:
        fecha_limite = self.fechas_limite.filter(etapa=FechaLimite.Etapa.POSTULACION).first()
        return self.activo and fecha_limite is not None and timezone.now() <= fecha_limite.fecha


# Tabla que contiene las fechas limites de los eventos, para cada etapa del proceso de postulación y revisión de artículos.
class FechaLimite(models.Model):
    class Etapa(models.TextChoices):
        POSTULACION = 'postulacion', 'Postulación'
        REVISION = 'revision', 'Revisión'
        VERSION_CORREGIDA = 'version_corregida', 'Versión corregida'
        VERSION_FINAL = 'version_final', 'Versión final'

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='fechas_limite')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='fechas_limite')
    etapa = models.CharField(max_length=20, choices=Etapa.choices)
    fecha = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['evento', 'etapa'], name='fecha_limite_unica_por_etapa'),
        ]

    def __str__(self):
        return f'{self.evento}: {self.get_etapa_display()}'



