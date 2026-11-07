from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Evento
from .permissions import PermisoEventos
from .serializers import EventoSerializer


@extend_schema_view(
    list=extend_schema(
        summary='Listar conferencias',
        description='Disponible para cualquier usuario con sesión. Permite buscar por nombre.',
        parameters=[OpenApiParameter('buscar', str, description='Busca por nombre')],
    ),
    create=extend_schema(
        summary='Crear conferencia',
        description='Solo con rol activo de administrador o comité.',
    ),
    retrieve=extend_schema(
        summary='Consultar una conferencia',
        description='Disponible para cualquier usuario con sesión.',
    ),
    partial_update=extend_schema(
        summary='Editar conferencia',
        description='Solo con rol activo de administrador o comité.',
    ),
)
class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated, PermisoEventos]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        eventos = Evento.objects.all()
        buscar = self.request.query_params.get('buscar')
        if buscar:
            eventos = eventos.filter(nombre__icontains=buscar)
        return eventos
