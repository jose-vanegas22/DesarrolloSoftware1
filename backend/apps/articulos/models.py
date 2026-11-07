from django.conf import settings
from django.db import models


class Articulo(models.Model):
    class LineaTematica(models.TextChoices):
        SISTEMAS_INTELIGENTES = 'sistemas_inteligentes', 'Sistemas Inteligentes'
        TECNOLOGIAS_INFORMATICA = 'tecnologias_informatica', 'Tecnologías en Informática'
        EDUCACION_INFORMATICA = 'educacion_informatica', 'Educación en Informática'
        SISTEMAS_SOFTWARE = 'sistemas_software', 'Sistemas de Software'
        SOFTWARE_PRACTICA = 'software_practica', 'Software en la práctica'

    class Estado(models.TextChoices):
        POSTULADO = 'postulado', 'Postulado'
        EN_REVISION = 'en_revision', 'En revisión'
        ACEPTADO = 'aceptado', 'Aceptado'
        RECHAZADO = 'rechazado', 'Rechazado'

    evento = models.ForeignKey('eventos.Evento', on_delete=models.PROTECT, related_name='articulos') # Evita borrar eventos que tengan articulos asociados
    autor_responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='articulos') # Evita borrar usuarios que tengan articulos asociados
    titulo = models.CharField(max_length=255)
    resumen = models.TextField()
    palabras_clave = models.CharField(max_length=255)
    linea_tematica = models.CharField(max_length=30, choices=LineaTematica.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.POSTULADO)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return self.titulo


# Autores del artículo. Pueden no tener cuenta en Conecta.
class Autor(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='autores')
    nombre = models.CharField(max_length=200)
    afiliacion = models.CharField(max_length=200)
    correo = models.EmailField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['articulo', 'correo'], name='autor_unico_por_articulo'),
        ]

    def __str__(self):
        return self.nombre
