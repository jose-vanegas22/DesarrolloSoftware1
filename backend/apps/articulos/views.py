from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Articulo
from .permissions import PermisoArticulos
from .serializers import ArticuloSerializer


@extend_schema_view(
    create=extend_schema(
        summary='Registrar artículo',
        description='Solo con rol activo de autor y dentro del plazo de postulación.',
    ),
)
class ArticuloViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet): # El post viene heredado de CreateModelMixin y el resto de GenericViewSet
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer
    permission_classes = [IsAuthenticated, PermisoArticulos]
