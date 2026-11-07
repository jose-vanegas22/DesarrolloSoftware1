from rest_framework.routers import SimpleRouter

from .views import EventoViewSet

router = SimpleRouter()
router.register('eventos', EventoViewSet)

urlpatterns = router.urls
