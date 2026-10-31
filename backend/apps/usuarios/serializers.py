from datetime import timedelta
from math import ceil
from django.conf import settings
from django.contrib.auth import password_validation
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario
from .services import verificar_captcha



class UsuarioSerializer(serializers.ModelSerializer): # Serializer para el modelo de usuario personalizado, que se utilizará para serializar y deserializar los datos del usuario en las vistas de la API
    password = serializers.CharField(write_only=True, required=False) # Campo de contraseña que no se mostrará al serializar el objeto, pero se requerirá al crear o actualizar un usuario

    class Meta:
        model = Usuario
        fields = [
            'id', 'correo', 'password', 'nombres', 'apellidos', 'telefono',
            'es_administrador', 'es_comite', 'es_autor',
            'correo_verificado', 'activo', 'last_login', 'creado', 'actualizado',
        ]
        read_only_fields = ['correo_verificado', 'last_login', 'creado', 'actualizado'] # Campos que no se podrán modificar al crear o actualizar un usuario

    def validate_password(self, value): # Validación de la contraseña utilizando las reglas de validación de Django
        password_validation.validate_password(value)
        return value

    def validate(self, attrs): # Validación de los roles del usuario y de la contraseña al crear o actualizar un usuario
        roles = [
            attrs.get('es_administrador', getattr(self.instance, 'es_administrador', False)), # attrs.get() obtiene el valor del atributo si está presente en los datos de entrada, o utiliza getattr() para obtener el valor del atributo del objeto de instancia si no está presente en los datos de entrada. Si el objeto de instancia es None (es decir, se está creando un nuevo usuario), se utiliza False como valor predeterminado.
            attrs.get('es_comite', getattr(self.instance, 'es_comite', False)),
            attrs.get('es_autor', getattr(self.instance, 'es_autor', False)),
        ] # Es una lista de booleanos [False, False, True], simplemente es un autor y ya
        if not any(roles):
            raise serializers.ValidationError('El usuario debe tener al menos un rol.')
        if self.instance is None and not attrs.get('password'): # Si se está creando un nuevo usuario (self.instance es None) y no se proporciona una contraseña en los datos de entrada (attrs.get('password') es None), se lanza una excepción de validación indicando que la contraseña es obligatoria.
            raise serializers.ValidationError({'password': 'La contraseña es obligatoria.'})
        return attrs

    # Se sobreescribe la conttraseña para lograr encriptarla y no guardarla en texto plano, además de poder actualizarla
    def create(self, validated_data): # Como se guarda un usuario nuevo
        password = validated_data.pop('password') # Saca la contraseña del diccionario validated_data para que no se guarde en texto plano en la base de datos
        return Usuario.objects.create_user(password=password, **validated_data)

    # Esta seria la forma de actualizar un usuario
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None) # Saca la contraseña del diccionario si vino sino se deja en None
        usuario = super().update(instance, validated_data) # Super deja que se actualicen los demás campos del usuario, y luego se actualiza la contraseña si vino en los datos de entrada
        if password: # Solo si se envio una contraseña nueva se encripta y se guarda
            usuario.set_password(password)
            usuario.save()
        return usuario

# Esta clase seria para lo que usa un usuario normal en nuestro caso seria autor
class DatosPersonalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'correo', 'nombres', 'apellidos', 'telefono', 'es_administrador', 'es_comite', 'es_autor']
        read_only_fields = ['id', 'correo', 'es_administrador', 'es_comite', 'es_autor']


class LoginSerializer(TokenObtainPairSerializer): # Heredamos el token para añadirle nuevas validaciones
    captcha = serializers.CharField(write_only=True) # Captcha como nuevo campos obligatorio

    def validate(self, attrs):
        request = self.context.get('request')
        ip = request.META.get('REMOTE_ADDR') if request else None
        if not verificar_captcha(attrs['captcha'], ip):
            raise serializers.ValidationError({'captcha': 'La verificación CAPTCHA no es válida.'})

        usuario = Usuario.objects.filter(correo=attrs['correo']).first()
        ahora = timezone.now()

        # Revisa si la cuenta no esta bloqueada o que
        if usuario and usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
            minutos = ceil((usuario.bloqueado_hasta - ahora).total_seconds() / 60)
            raise AuthenticationFailed(
                f'Cuenta bloqueada por demasiados intentos fallidos. Intenta de nuevo en {minutos} minuto(s).'
            )

        try:
            datos = super().validate(attrs) # Revisa el correo y la contraseña para generar los tokens
        except AuthenticationFailed:
            if usuario:
                usuario.intentos_fallidos += 1
                if usuario.intentos_fallidos >= settings.LOGIN_MAX_INTENTOS:
                    usuario.bloqueado_hasta = ahora + timedelta(minutes=settings.LOGIN_MINUTOS_BLOQUEO)
                    usuario.intentos_fallidos = 0
                usuario.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
            raise

        if self.user.intentos_fallidos or self.user.bloqueado_hasta:
            self.user.intentos_fallidos = 0
            self.user.bloqueado_hasta = None
            self.user.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])

        return datos

