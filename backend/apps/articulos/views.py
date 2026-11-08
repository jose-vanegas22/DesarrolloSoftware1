from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from apps.usuarios.permissions import es_gestor, obtener_rol_activo
from .models import Articulo
from .permissions import PermisoArticulos
from .serializers import ArticuloSerializer


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

    create=extend_schema(
        summary='Registrar artículo',
        description='Solo con rol activo de autor y dentro del plazo de postulación.',
    ),
)
class ArticuloViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet): # El post viene heredado de CreateModelMixin y el resto de GenericViewSet, ListModelMixin agrega el GET para listar
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer
    permission_classes = [IsAuthenticated, PermisoArticulos]


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
