from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView
from apps.usuarios.views import LoginView


urlpatterns = [
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('apps.usuarios.urls')),  # Incluye las rutas de la app usuarios
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'), # Genera la descripcion de la API en formaro OpenApi
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), # Es la pagina swagger que se abre en el navegador
]