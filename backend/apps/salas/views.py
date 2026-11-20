from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Sala
from .serializers import SalaSerializer


@extend_schema_view(
    list=extend_schema(
        summary='Listar salas',
        description='Disponible para cualquier usuario con sesión iniciada.',
    ),
    create=extend_schema(
        summary='Registrar sala',
        description='Disponible para cualquier usuario con sesión iniciada. El nombre de la sala debe ser único.',
    ),
    retrieve=extend_schema(
        summary='Consultar una sala',
        description='Disponible para cualquier usuario con sesión iniciada.',
    ),
    partial_update=extend_schema(
        summary='Editar sala',
        description='Disponible para cualquier usuario con sesión iniciada. Permite cambiar el nombre y la capacidad; el estado no se modifica aquí.',
    ),
)
class SalaViewSet(viewsets.ModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
