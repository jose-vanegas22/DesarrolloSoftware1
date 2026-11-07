from rest_framework.permissions import BasePermission
from .models import ROLES


def obtener_rol_activo(request): # Para saber con que rol entro
    rol = request.auth.get('rol_activo') if request.auth else None 
    if rol in ROLES and getattr(request.user, f'es_{rol}', False):
        return rol
    return None

def es_gestor(request):
    return obtener_rol_activo(request) in ('administrador', 'comite')


# Tiene 2 funciones porque el DRF revisa los permisos en dos momentos de la aplicacion
class PermisoUsuarios(BasePermission):
    # listar, crear y borrar quedan solo para gestores. Consultar o editar a un usuario concreto pasa a la segunda revisión.
    def has_permission(self, request, view):
        return view.action in ('retrieve', 'update', 'partial_update') or es_gestor(request)

    # un gestor puede actuar sobre cualquier usuario; los demás, solo sobre sí mismos.
    def has_object_permission(self, request, view, obj):
        return es_gestor(request) or obj == request.user

