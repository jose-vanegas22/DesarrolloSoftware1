from rest_framework.routers import SimpleRouter
from .views import ArticuloViewSet

router = SimpleRouter()
router.register('articulos', ArticuloViewSet)

urlpatterns = router.urls
