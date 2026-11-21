from django.db import models


class SalaQuerySet(models.QuerySet):
    def activas(self):
        return self.filter(activo=True)


class Sala(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    capacidad = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    objects = SalaQuerySet.as_manager()

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
