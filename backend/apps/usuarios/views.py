from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Usuario
from .permissions import PermisoUsuarios, es_gestor
from .serializers import DatosPersonalesSerializer, UsuarioSerializer, LoginSerializer
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework_simplejwt.views import TokenObtainPairView



@extend_schema_view(
    list=extend_schema(parameters=[
        OpenApiParameter('rol', str, enum=['administrador', 'comite', 'autor'], description='Filtra por rol'),
        OpenApiParameter('activo', bool, description='Filtra por usuarios activos o inactivos'),
        OpenApiParameter('buscar', str, description='Busca en nombres, apellidos y correo'),
    ])
)
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    permission_classes = [IsAuthenticated, PermisoUsuarios] # Primero exigimos sesion iniciada y luego revisamos si es autor o gestor, si es autor solo puede ver y editar su propio perfil, si es gestor puede ver y editar cualquier perfil

    def get_serializer_class(self): # Elige el serializer segun quien hace la peticion
        if getattr(self, 'swagger_fake_view', False):
            return UsuarioSerializer
        if self.action == 'perfil':
            return DatosPersonalesSerializer
        if self.action in ('update', 'partial_update') and not es_gestor(self.request.user):
            return DatosPersonalesSerializer
        return UsuarioSerializer

    def get_queryset(self): # Filtra los usuarios segun los parametros de la peticion, si es gestor puede ver todos los usuarios, si es autor solo puede ver su propio perfil
        usuarios = Usuario.objects.all() # Si es autor solo puede ver su propio perfil
        params = self.request.query_params # Obtiene los parametros de la peticion

        rol = params.get('rol')
        if rol == 'administrador':
            usuarios = usuarios.filter(es_administrador=True)
        elif rol == 'comite':
            usuarios = usuarios.filter(es_comite=True)
        elif rol == 'autor':
            usuarios = usuarios.filter(es_autor=True)

        activo = params.get('activo') # Filtra por usuarios activos o inactivos, si no se especifica, devuelve todos los usuarios
        if activo in ('true', 'false'):
            usuarios = usuarios.filter(activo=activo == 'true')

        buscar = params.get('buscar') # Busca por nombre, apellido o correo, si no se especifica, devuelve todos los usuarios
        if buscar:
            usuarios = usuarios.filter(
                Q(nombres__icontains=buscar) | Q(apellidos__icontains=buscar) | Q(correo__icontains=buscar)
            )

        return usuarios

    @action(detail=False, methods=['get', 'patch']) # Permite a los usuarios ver y editar su propio perfil, y a los gestores ver y editar cualquier perfil
    def perfil(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

