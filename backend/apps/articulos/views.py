from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.usuarios.permissions import es_gestor, obtener_rol_activo
from .models import Articulo, VersionArticulo
from .permissions import PermisoArticulos
from .serializers import ArticuloDetalleSerializer, ArticuloSerializer, VersionArticuloSerializer
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError



@extend_schema_view(
    list=extend_schema(
        summary='Consultar artículos',
        description='Administrador y comité ven todos los artículos; el autor solo los propios. No incluye deshabilitados.',
        parameters=[
            OpenApiParameter('buscar', str, description='Busca por título'),
            OpenApiParameter('autor', str, description='Busca por nombre de cualquier autor. Solo administrador y comité'),
            OpenApiParameter('estado', str, description='Estado del artículo'),
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
)
class ArticuloViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet): # El post viene heredado de CreateModelMixin y el resto de GenericViewSet, ListModelMixin agrega el GET para listar
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer
    permission_classes = [IsAuthenticated, PermisoArticulos]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArticuloDetalleSerializer
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

        if buscar:
            articulos = articulos.filter(titulo__icontains=buscar)
        if autor and es_gestor(self.request):
            articulos = articulos.filter(autores__nombre__icontains=autor).distinct()
        if estado:
            articulos = articulos.filter(estado=estado)
        return articulos



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


