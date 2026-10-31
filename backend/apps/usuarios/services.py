# Usamos un documento llamado service.py porque es el nombre comun para la logica de negocio que no es un modelo, como comunicarse con un servidor externo
import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

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
