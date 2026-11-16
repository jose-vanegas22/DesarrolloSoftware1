# Usamos un documento llamado service.py porque es el nombre comun para la logica de negocio que no es un modelo, como comunicarse con un servidor externo
import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import CodigoRecuperacion, Usuario

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

