from rest_framework.permissions import BasePermission
from apps.usuarios.permissions import obtener_rol_activo

# Solo deja pasar a quien haya entrado con el rol de autor
class PermisoArticulos(BasePermission):
    def has_permission(self, request, view): # DERF ejecuta esta funcion automaticamente antes de atender cada peticion, request es la peticion con el usuario y el token
        rol = obtener_rol_activo(request) # Lee el rol y lo guarda
        if view.action == 'list': # Si la accion es listar, solo deja pasar a los autores
            return rol is not None
        return rol == 'autor'
