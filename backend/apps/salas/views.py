from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Sala
from .permissions import PermisoSalas
from .serializers import SalaSerializer


@extend_schema_view(
    list=extend_schema(
        summary='Listar salas',
        description='Disponible para cualquier usuario con sesión iniciada. Permite filtrar por estado con activo=true o activo=false.',
        parameters=[OpenApiParameter('activo', bool, description='Filtra por salas activas o inactivas')],
    ),
    create=extend_schema(
        summary='Registrar sala',
        description='Solo con rol activo de administrador o comité. El nombre de la sala debe ser único.',
    ),
    retrieve=extend_schema(
        summary='Consultar una sala',
        description='Disponible para cualquier usuario con sesión iniciada.',
    ),
    partial_update=extend_schema(
        summary='Editar sala',
        description='Solo con rol activo de administrador o comité. Permite cambiar el nombre y la capacidad; el estado no se modifica aquí.',
    ),
)
class SalaViewSet(viewsets.ModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    permission_classes = [IsAuthenticated, PermisoSalas]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        salas = Sala.objects.all()
        activo = self.request.query_params.get('activo')
        if activo == 'true':
            salas = salas.activas()
        elif activo == 'false':
            salas = salas.filter(activo=False)
        return salas

    @extend_schema(
        summary='Activar sala',
        description='Solo con rol activo de administrador o comité. Marca la sala como activa para que pueda usarse al programar sesiones de la agenda.',
        request=None,
    )
    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None):
        sala = self.get_object()
        sala.activo = True
        sala.save(update_fields=['activo'])
        return Response(self.get_serializer(sala).data)

    @extend_schema(
        summary='Desactivar sala',
        description='Solo con rol activo de administrador o comité. Marca la sala como inactiva; deja de estar disponible para nuevas sesiones de la agenda.',
        request=None,
    )
    @action(detail=True, methods=['post'], url_path='desactivar')
    def desactivar(self, request, pk=None):
        sala = self.get_object()
        sala.activo = False
        sala.save(update_fields=['activo'])
        return Response(self.get_serializer(sala).data)
