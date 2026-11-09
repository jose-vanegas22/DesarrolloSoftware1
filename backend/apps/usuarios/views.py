from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Usuario
from .permissions import PermisoUsuarios, es_gestor
from .serializers import (
    DatosPersonalesSerializer,
    LoginSerializer,
    RegistroSerializer,
    SeleccionarRolSerializer,
    SesionSerializer,
    UsuarioSerializer,
)
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken




@extend_schema_view(
    list=extend_schema(
        summary='Listar usuarios',
        description='Disponible para cualquier usuario con sesión. Se puede filtrar por rol, estado y texto.',
        parameters=[
            OpenApiParameter('rol', str, enum=['administrador', 'comite', 'autor'], description='Filtra por rol'),
            OpenApiParameter('activo', bool, description='Filtra por usuarios activos o inactivos'),
            OpenApiParameter('buscar', str, description='Busca en nombres, apellidos y correo'),
        ],
    ),
    create=extend_schema(
        summary='Crear usuario',
        description='Solo administradores y miembros del comité. El usuario debe tener al menos un rol.',
    ),
    retrieve=extend_schema(
        summary='Consultar un usuario',
        description='Disponible para cualquier usuario con sesión.',
    ),
    update=extend_schema(
        summary='Actualizar usuario (completo)',
        description='Administradores y comité pueden editar a cualquier usuario. '
                    'Los demás solo pueden editar sus propios nombres, apellidos y teléfono.',
    ),
    partial_update=extend_schema(
        summary='Actualizar usuario (parcial)',
        description='Mismas reglas que la actualización completa, pero solo se envían los campos a cambiar.',
    ),
    destroy=extend_schema(
        summary='Borrar usuario',
        description='Solo administradores y miembros del comité. No se puede borrar al administrador '
                    'ni a usuarios que sean autores responsables de artículos.',
    ),

)
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    permission_classes = [IsAuthenticated, PermisoUsuarios] # Primero exigimos sesion iniciada y luego revisamos si es autor o gestor, si es autor solo puede ver y editar su propio perfil, si es gestor puede ver y editar cualquier perfil

    def get_serializer_class(self): # Sirve para guiar a cual seriaalizers llegar
        if self.action == 'seleccionar_rol':
            return SeleccionarRolSerializer
        if self.action == 'registro':
            return RegistroSerializer
        if self.action == 'perfil':
            return DatosPersonalesSerializer
        if getattr(self, 'swagger_fake_view', False):
            return UsuarioSerializer
        if self.action in ('update', 'partial_update') and not es_gestor(self.request):
            return DatosPersonalesSerializer
        return UsuarioSerializer

    # Para que no se puede borrar el unico administrador del sistema
    def perform_destroy(self, instance):
        if instance.es_administrador:
            raise ValidationError({'detail': 'No se puede borrar al administrador del sistema.'})
        if instance.articulos.exists():
            raise ValidationError({'detail': 'No se puede borrar porque es autor responsable de artículos. Desactívalo en su lugar.'})
        instance.delete()

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

    @extend_schema(methods=['GET'], summary='Ver mi perfil',
                   description='Devuelve los datos y roles del usuario que inició sesión.')
    @extend_schema(methods=['PATCH'], summary='Editar mi perfil',
                   description='Permite cambiar nombres, apellidos y teléfono del usuario que inició sesión.')
    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated]) # Permite a los usuarios ver y editar su propio perfil, y a los gestores ver y editar cualquier perfil
    def perfil(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # endpoint para que las personas creen usuarios pero solo como autores
    @extend_schema(
        summary='Registrarse como autor',
        description='Endpoint público (no requiere sesión). Crea un usuario con rol autor; '
                    'los roles enviados se ignoran. Requiere el token de reCAPTCHA en el campo captcha.',
        responses={201: RegistroSerializer},
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], authentication_classes=[])
    def registro(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @extend_schema(
        summary='Seleccionar rol activo',
        description='Recibe uno de los roles del usuario y devuelve tokens nuevos con ese rol activo. '
                    'Los permisos de la sesión dependen del rol activo.',
        responses={200: SesionSerializer},
    )
    @action(detail=False, methods=['post'], url_path='seleccionar-rol', permission_classes=[IsAuthenticated])
    def seleccionar_rol(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = RefreshToken.for_user(request.user)
        refresh['rol_activo'] = serializer.validated_data['rol']
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'roles': request.user.roles,
            'rol_activo': refresh['rol_activo'],
        })


@extend_schema_view(
    post=extend_schema(
        summary='Iniciar sesión',
        description='Recibe correo, contraseña y token de reCAPTCHA, y devuelve los tokens access y refresh. '
                    'Tras 5 intentos fallidos, la cuenta se bloquea 15 minutos.'
                    'Si el usuario tiene un solo rol, queda como rol activo; si tiene varios, rol_activo es null '
                    'y debe elegir uno en /api/usuarios/seleccionar-rol/.',
        responses={200: SesionSerializer},
    )
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

