from rest_framework.routers import SimpleRouter
from .views import UsuarioViewSet

router = SimpleRouter() # Crea el router para las rutas de la API
# Esta es la linea clave, lo que hace es revisar todos los metodos de UsuarioViewSet y crear una ruta para cada uno
router.register('usuarios', UsuarioViewSet) 

# Django siempre busca una variable llamada urlpatterns en cada urls.py, asi que la creamos y le asignamos las urls del router
urlpatterns = router.urls
