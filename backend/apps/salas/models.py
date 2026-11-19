from django.db import models


class Sala(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    capacidad = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
