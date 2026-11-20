from django.db import transaction
from django.db.models import ProtectedError
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.usuarios.permissions import es_gestor, obtener_rol_activo
from .models import Articulo, AsignacionRevision, Revision, VersionArticulo
from .permissions import PermisoArticulos
from .serializers import (
    ArticuloDetalleSerializer,
    ArticuloEdicionSerializer,
    ArticuloSerializer,
    AsignacionRevisionSerializer,
    AsignarRevisoresSerializer,
    ReemplazoPdfSerializer,
    VersionArticuloSerializer,
    RevisionSerializer,
)
from .services import registrar_revision
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError



@extend_schema_view(
    list=extend_schema(
        summary='Consultar artículos',
        description='Administrador y comité ven todos los artículos; el autor solo los propios. No incluye deshabilitados.',
        parameters=[
            OpenApiParameter('buscar', str, description='Busca por título'),
            OpenApiParameter('autor', str, description='Busca por nombre de cualquier autor. Solo administrador y comité'),
            OpenApiParameter('estado', str, description='Estado del artículo'),
            OpenApiParameter('evento', int, description='Id de la conferencia'),
        ],
    ),

    retrieve=extend_schema(
        summary='Ver detalle del artículo',
        description='Administrador y comité ven cualquier artículo; el autor solo los propios. No incluye deshabilitados.',
    ),


    create=extend_schema(
        summary='Registrar artículo',
        description='Solo con rol activo de autor y dentro del plazo de postulación.',
    ),

    partial_update=extend_schema(
        summary='Modificar artículo',
        description='Solo el autor responsable, con rol activo de autor y dentro del plazo de postulación. Permite cambiar título, resumen, palabras clave y línea temática; el estado no se puede modificar.',
    ),
)
class ArticuloViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet): # El post viene heredado de CreateModelMixin y el resto de GenericViewSet, ListModelMixin agrega el GET para listar
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer
    permission_classes = [IsAuthenticated, PermisoArticulos]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArticuloDetalleSerializer
        if self.action == 'partial_update':
            return ArticuloEdicionSerializer
        return super().get_serializer_class()

    # Nos permite filtrar los articulos que se devuelven en la lista, dependiendo del rol del usuario y de los parametros de busqueda que se le pasen en 
    #la url
    def get_queryset(self):
        articulos = Articulo.objects.filter(activo=True).select_related('evento') # filter saca los deshabilitados

        if obtener_rol_activo(self.request) == 'autor':
            articulos = articulos.filter(autor_responsable=self.request.user)

        buscar = self.request.query_params.get('buscar')
        autor = self.request.query_params.get('autor')
        estado = self.request.query_params.get('estado')
        evento = self.request.query_params.get('evento')


        if buscar:
            articulos = articulos.filter(titulo__icontains=buscar)
        if autor and es_gestor(self.request):
            articulos = articulos.filter(autores__nombre__icontains=autor).distinct()
        if estado:
            articulos = articulos.filter(estado=estado)
        if evento and evento.isdigit():  # Solo numeros, para que un valor raro no cause error
            articulos = articulos.filter(evento_id=evento)
        return articulos

    @extend_schema(
        summary='Evaluar artículo',
        description='Solo comité asignado, sin autoría propia, tras cerrar postulaciones y hasta el límite de revisión. Una evaluación por asignación. El resultado se calcula al registrar las tres evaluaciones: con dos o más votos iguales se acepta o se rechaza.',
        request=RevisionSerializer,
        responses={201: RevisionSerializer},
    )
    @action(detail=True, methods=['post'], url_path='evaluacion', serializer_class=RevisionSerializer)
    def evaluar(self, request, pk=None):
        articulo = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        revision = registrar_revision(request, articulo, serializer.validated_data)
        return Response(RevisionSerializer(revision).data, status=status.HTTP_201_CREATED)


    @extend_schema(
        summary='Consultar evaluaciones del artículo',
        description='Solo con rol activo de autor y únicamente para artículos propios. Devuelve las '
                    'evaluaciones registradas del artículo sin exponer la identidad de los revisores. '
                    'Un artículo ajeno o inexistente responde 404.',
        responses={200: RevisionSerializer(many=True)},
    )
    @action(detail=True, methods=['get'], url_path='evaluaciones')
    def evaluaciones(self, request, pk=None):
        # get_queryset limita al autor a sus propios artículos, por lo que un artículo ajeno responde 404.
        articulo = self.get_object()
        revisiones = Revision.objects.filter(asignacion__articulo=articulo)
        return Response(RevisionSerializer(revisiones, many=True).data)


    @extend_schema(
        summary='Deshabilitar artículo', request=None, responses={204: None},
        description='Solo con rol activo de administrador o comité. Retira el artículo de las consultas '
        'sin borrar sus autores ni versiones. La acción es irreversible: la API no permite reactivarlo. '
        'Devuelve 404 si el artículo no existe o ya está deshabilitado. La interfaz debe pedir confirmación previa.',
    )
    @action(detail=True, methods=['post'], url_path='deshabilitar')
    def deshabilitar(self, request, pk=None):
        articulo = self.get_object()
        # Solo cambia la disponibilidad; conserva el estado de revision y los datos asociados.
        articulo.activo = False
        articulo.save(update_fields=['activo', 'actualizado'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary='Subir PDF inicial',
                description='Solo el autor responsable, dentro del plazo de postulación. Solo PDF del tamaño máximo permitido.')
    @action(detail=True, methods=['post'], url_path='pdf', serializer_class=VersionArticuloSerializer, parser_classes=[MultiPartParser])
    def pdf(self, request, pk=None):
        articulo = self.get_object()
        contexto = {**self.get_serializer_context(), 'articulo': articulo}
        serializer = self.get_serializer(data=request.data, context=contexto)
        serializer.is_valid(raise_exception=True)
        serializer.save(articulo=articulo, tipo=VersionArticulo.Tipo.INICIAL)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



    @extend_schema(summary='Quitar coautor', request=None, responses={204: None},
                parameters=[OpenApiParameter('autor_id', int, OpenApiParameter.PATH, description='Id del coautor')],
                description='Solo el autor responsable y dentro del plazo de postulación. No permite quitar al autor responsable.')
    @action(detail=True, methods=['delete'], url_path=r'autores/(?P<autor_id>\d+)')
    def quitar_coautor(self, request, pk=None, autor_id=None):
        articulo = self.get_object()
        autor = get_object_or_404(articulo.autores, id=autor_id)

        if autor.correo.lower() == articulo.autor_responsable.correo.lower():
            raise ValidationError({'detail': 'No se puede quitar al autor responsable.'})
        if not articulo.evento.postulacion_abierta:
            raise ValidationError({'detail': 'La postulación de esta conferencia ya no está abierta.'})

        autor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    @extend_schema(
        methods=['GET'],
        summary='Consultar revisores asignados',
        description='Solo con rol activo de comite. Devuelve las asignaciones registradas del articulo.',
        responses={200: AsignacionRevisionSerializer(many=True)},
    )
    @extend_schema(
        methods=['POST'],
        summary='Asignar revisores',
        description='Solo con rol activo de comite. La postulacion debe estar cerrada y se deben enviar '
                    'exactamente tres miembros del comite (se recomienda priorizar especialistas en la linea tematica), '
                    'que no sean autores ni coautores y que no tengan ya tres articulos asignados.',
        request=AsignarRevisoresSerializer,
        responses={201: AsignacionRevisionSerializer(many=True)},
    )
    @action(detail=True, methods=['get', 'post'], url_path='revisores')
    def revisores(self, request, pk=None):
        articulo = self.get_object()

        if request.method == 'POST':
            contexto = {**self.get_serializer_context(), 'articulo': articulo}
            serializer = AsignarRevisoresSerializer(data=request.data, context=contexto)
            serializer.is_valid(raise_exception=True)
            revisores = serializer.validated_data['revisores']

            with transaction.atomic():
                actuales = {
                    asignacion.revisor_id: asignacion
                    for asignacion in articulo.asignaciones_revision.select_for_update()
                }
                ids = {revisor.id for revisor in revisores}
                try:
                    articulo.asignaciones_revision.exclude(revisor_id__in=ids).delete()
                except ProtectedError:
                    raise ValidationError({'detail': 'No se puede quitar un revisor que ya evaluo el articulo.'})
                for revisor in revisores:
                    if revisor.id not in actuales:
                        AsignacionRevision.objects.create(articulo=articulo, revisor=revisor)
                        
                if articulo.estado == Articulo.Estado.POSTULADO:  # Con los tres revisores asignados empieza la revision
                    articulo.estado = Articulo.Estado.EN_REVISION
                    articulo.save(update_fields=['estado', 'actualizado'])

            asignaciones = articulo.asignaciones_revision.select_related('revisor').order_by('creado', 'id')
            return Response(AsignacionRevisionSerializer(asignaciones, many=True).data, status=status.HTTP_201_CREATED)

        asignaciones = articulo.asignaciones_revision.select_related('revisor').order_by('creado', 'id')
        return Response(AsignacionRevisionSerializer(asignaciones, many=True).data)


    @extend_schema(summary='Reemplazar el PDF inicial',
        description='Solo el autor responsable, dentro del plazo de postulación. Guarda una versión nueva; '
        'la anterior se conserva en el historial.')
    @action(detail=True, methods=['patch'], url_path='reemplazar-pdf', serializer_class=ReemplazoPdfSerializer,
            parser_classes=[MultiPartParser])
    def reemplazar_pdf(self, request, pk=None):
        articulo = self.get_object()
        contexto = {**self.get_serializer_context(), 'articulo': articulo}
        serializer = self.get_serializer(data=request.data, context=contexto)
        serializer.is_valid(raise_exception=True)
        serializer.save(articulo=articulo, tipo=VersionArticulo.Tipo.INICIAL)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        articulo = self.get_object()
        if not articulo.evento.postulacion_abierta:
            raise ValidationError({'detail': 'La postulación de esta conferencia ya no está abierta; el artículo no se puede modificar.'})
        serializer = self.get_serializer(articulo, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


