from rest_framework.permissions import BasePermission
from apps.usuarios.permissions import obtener_rol_activo

# Solo deja pasar a quien haya entrado con el rol de autor
class PermisoArticulos(BasePermission):
    def has_permission(self, request, view): # DERF ejecuta esta funcion automaticamente antes de atender cada peticion, request es la peticion con el usuario y el token
        rol = obtener_rol_activo(request) # Lee el rol y lo guarda
        if view.action in ('list', 'retrieve'): # Consultar la lista o el detalle se permite a cualquier rol valido
            return rol is not None
        return rol == 'autor'
