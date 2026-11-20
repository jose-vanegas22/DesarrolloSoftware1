from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from .models import ROLES


def obtener_rol_activo(request): # Para saber con que rol entro
    rol = request.auth.get('rol_activo') if request.auth else None 
    if rol in ROLES and getattr(request.user, f'es_{rol}', False):
        return rol
    return None

def es_gestor(request):
    return obtener_rol_activo(request) in ('administrador', 'comite')

def es_administrador(request):
    return obtener_rol_activo(request) == 'administrador'


def cambian_las_especialidades(usuario, datos):
    # Solo importa si la peticion intenta dejar las especialidades distintas a las que ya tiene.
    # Asi un comite puede editar otros campos aunque el formulario reenvie las especialidades actuales.
    if 'especialidades' not in datos:
        return False
    nuevas = datos.get('especialidades')
    if not isinstance(nuevas, list):
        return True # Formato invalido: se deja que el serializer responda el 400 correspondiente
    actuales = usuario.especialidades or []
    return sorted(map(str, nuevas)) != sorted(map(str, actuales))


# Tiene 2 funciones porque el DRF revisa los permisos en dos momentos de la aplicacion
class PermisoUsuarios(BasePermission):
    # listar, crear y borrar quedan solo para gestores. Consultar o editar a un usuario concreto pasa a la segunda revisión.
    def has_permission(self, request, view):
        if view.action in ('retrieve', 'update', 'partial_update'):
            return True
        if not es_gestor(request):
            return False
        if view.action == 'create' and request.data.get('especialidades') and not es_administrador(request):
            raise PermissionDenied('Solo el administrador puede asignar especialidades.')
        return True

    # un gestor puede actuar sobre cualquier usuario; los demás, solo sobre sí mismos.
    def has_object_permission(self, request, view, obj):
        if view.action in ('update', 'partial_update') and not es_administrador(request):
            if cambian_las_especialidades(obj, request.data):
                raise PermissionDenied('Solo el administrador puede asignar o modificar especialidades.')
        return es_gestor(request) or obj == request.user

