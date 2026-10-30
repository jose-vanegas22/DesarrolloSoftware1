from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _crear_usuario(self, correo, password, **extra_fields):
        if not correo:
            raise ValueError('El correo es obligatorio')
        usuario = self.model(correo=self.normalize_email(correo), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, correo, password=None, **extra_fields):
        return self._crear_usuario(correo, password, **extra_fields)

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault('es_administrador', True)
        return self._crear_usuario(correo, password, **extra_fields)


class Usuario(AbstractBaseUser): # Heredamos de AbstractBaseUser para crear un modelo de usuario personalizado
    correo = models.EmailField('correo electrónico', unique=True)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20, blank=True)
    es_administrador = models.BooleanField(default=False)
    es_comite = models.BooleanField(default=False)
    es_autor = models.BooleanField(default=False)
    correo_verificado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    EMAIL_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombres', 'apellidos']

    class Meta:
        ordering = ['nombres', 'apellidos']

    def __str__(self):
        return f'{self.nombres} {self.apellidos} ({self.correo})'

    @property
    def is_active(self):
        return self.activo


class CodigoRecuperacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='codigos_recuperacion')
    pin = models.CharField(max_length=128)
    creado = models.DateTimeField(auto_now_add=True)
    expira = models.DateTimeField()
    intentos = models.PositiveSmallIntegerField(default=0)
    usado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f'Código de {self.usuario.correo} ({self.creado:%Y-%m-%d %H:%M})'
