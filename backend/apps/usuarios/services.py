# Usamos un documento llamado service.py porque es el nombre comun para la logica de negocio que no es un modelo, como comunicarse con un servidor externo
import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.core.mail import send_mail
from django.utils import timezone

from .models import CodigoRecuperacion, Usuario

import logging
from smtplib import SMTPException

logger = logging.getLogger(__name__) # Sirve para registrar errores en este caso para cuando un correo no se envie

NOMBRES_ROLES = {'administrador': 'Administrador', 'comite': 'Comité científico', 'autor': 'Autor'} # Diccionario para envir el rol en el mensaje de una forma mas presentable

# URL de verificación de reCAPTCHA para el backend. Esta URL se utiliza para enviar la solicitud de verificación del token de reCAPTCHA al servidor de Google y obtener la respuesta correspondiente.
URL_VERIFICACION = 'https://www.google.com/recaptcha/api/siteverify' 


def verificar_captcha(token, ip=None):
    datos = {'secret': settings.RECAPTCHA_SECRET_KEY, 'response': token}
    if ip:
        datos['remoteip'] = ip
    try:
        with urlopen(URL_VERIFICACION, data=urlencode(datos).encode(), timeout=5) as respuesta:
            resultado = json.load(respuesta)
    except (URLError, TimeoutError, ValueError):
        return False
    return resultado.get('success', False)


# Genera un codigo de 6 digitos, lo guarda cifrado y lo envia al correo.
# Si el correo no existe o la cuenta esta inactiva no hace nada, para no revelar que correos existen.
def enviar_codigo_recuperacion(correo):
    usuario = Usuario.objects.filter(correo__iexact=correo, activo=True).first()
    if usuario is None:
        return

    usuario.codigos_recuperacion.filter(usado=False).update(usado=True)  # Los codigos anteriores dejan de servir

    pin = f'{secrets.randbelow(1_000_000):06d}' # Nos da un numero al azar en ese rango
    minutos = settings.CODIGO_RECUPERACION_MINUTOS
    CodigoRecuperacion.objects.create(
        usuario=usuario,
        pin=make_password(pin), # Nos ayuda a cifrarlo para que no se guarde en la base de datos tal cual
        expira=timezone.now() + timedelta(minutes=minutos),
    )
    send_mail( # Nos permite enviar un correo al usuario
        'Código de recuperación de Conecta',
        f'Hola {usuario.nombres}, tu código de recuperación es {pin}. Vence en {minutos} minutos.\n'
        'Si no solicitaste este código, ignora este correo.',
        None,
        [usuario.correo],
    )



# Cambia la contraseña si el codigo es valido. Devuelve True si se cambio y False si el codigo no sirve.
@transaction.atomic
def restablecer_contrasena(correo, pin, password):
    usuario = Usuario.objects.filter(correo__iexact=correo, activo=True).first()
    if usuario is None:
        return False

    codigo = usuario.codigos_recuperacion.filter(usado=False, expira__gt=timezone.now()).first()
    if codigo is None:
        return False

    if not check_password(pin, codigo.pin):  # Compara el numero escrito con el cifrado
        codigo.intentos += 1
        if codigo.intentos >= settings.CODIGO_RECUPERACION_MAX_INTENTOS:
            codigo.usado = True  # Tras 5 intentos fallidos el codigo deja de servir
        codigo.save(update_fields=['intentos', 'usado'])
        return False

    usuario.set_password(password)
    usuario.intentos_fallidos = 0  # Si estaba bloqueado por intentos de login, se desbloquea
    usuario.bloqueado_hasta = None
    usuario.save(update_fields=['password', 'intentos_fallidos', 'bloqueado_hasta'])

    codigo.usado = True
    codigo.save(update_fields=['usado'])

    for token in OutstandingToken.objects.filter(user=usuario):  # Cierra todas las sesiones abiertas
        BlacklistedToken.objects.get_or_create(token=token)
    return True




# Avisa por correo que la cuenta fue creada. Nunca incluye la contraseña.
# Si el envio falla, solo se registra el error: la cuenta ya quedo creada.
def enviar_correo_bienvenida(usuario, creado_por_gestor=False):
    roles = ', '.join(NOMBRES_ROLES[rol] for rol in usuario.roles)
    mensaje = (
        f'Hola {usuario.nombres}, tu cuenta en Conecta fue creada.\n\n'
        f'Roles: {roles}\n'
        f'Inicia sesión con tu correo en: {settings.FRONTEND_URL}/login\n'
    )
    if creado_por_gestor:
        mensaje += (
            '\nTu cuenta fue creada por el equipo organizador. Para definir tu propia contraseña, '
            'en la pantalla de inicio de sesión pulsa "¿Olvidaste tu contraseña?" y sigue los pasos.\n'
        )

    try:
        send_mail('Tu cuenta en Conecta fue creada', mensaje, None, [usuario.correo])
    except (SMTPException, OSError):
        logger.exception('No se pudo enviar el correo de bienvenida a %s', usuario.correo) # Nos permite atrapar los errores tipicos de enviar correos

