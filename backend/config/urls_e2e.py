"""Las rutas habituales mas archivos locales, solo con settings_e2e."""
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import path

from .urls import urlpatterns as rutas_api


def identificar_entorno(request):
    return JsonResponse({'base': settings.DATABASES['default']['NAME'],
                         'directorio': str(settings.E2E_DIR)})


# Solo existe con settings_e2e. No permite modificar datos ni evita el login.
urlpatterns = [path('api/e2e/entorno/', identificar_entorno),
               *rutas_api, *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)]
