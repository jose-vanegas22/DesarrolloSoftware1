from django.db import transaction
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Evento, FechaLimite
from .permissions import PermisoEventos
from .serializers import EventoSerializer, FechasLimiteSerializer



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


    @extend_schema(methods=['GET'], summary='Consultar fechas límite',
                   description='Disponible para cualquier usuario con sesión. Las etapas sin configurar devuelven null.')
    @extend_schema(methods=['PATCH'], summary='Configurar fechas límite',
                   description='Solo con rol activo de administrador o comité. Las etapas deben estar en orden cronológico.')
    @action(detail=True, methods=['get', 'patch'], url_path='fechas-limite', serializer_class=FechasLimiteSerializer)
    def fechas_limite(self, request, pk=None):
        evento = self.get_object()

        if request.method == 'PATCH':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                for etapa, fecha in serializer.validated_data.items():
                    FechaLimite.objects.update_or_create(
                        evento=evento,
                        etapa=etapa,
                        defaults={'fecha': fecha, 'creado_por': request.user},
                    )
            return Response(serializer.data)

        fechas = {fecha.etapa: fecha.fecha for fecha in evento.fechas_limite.all()}
        serializer = self.get_serializer({etapa: fechas.get(etapa) for etapa in FechaLimite.Etapa.values})
        return Response(serializer.data)
