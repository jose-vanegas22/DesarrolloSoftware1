from rest_framework.routers import SimpleRouter

from .views import SalaViewSet

router = SimpleRouter()
router.register('salas', SalaViewSet)

urlpatterns = router.urls
