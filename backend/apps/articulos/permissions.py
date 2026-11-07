from rest_framework.permissions import BasePermission
from apps.usuarios.permissions import obtener_rol_activo

# Solo deja pasar a quien haya entrado con el rol de autor
class PermisoArticulos(BasePermission):
    def has_permission(self, request, view):
        return obtener_rol_activo(request) == 'autor'
