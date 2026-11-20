from rest_framework.permissions import BasePermission
from apps.usuarios.permissions import es_gestor, obtener_rol_activo

# Los permisos dependen de la accion y del rol activo de la sesion.
class PermisoArticulos(BasePermission):
    def has_permission(self, request, view): # DERF ejecuta esta funcion automaticamente antes de atender cada peticion, request es la peticion con el usuario y el token
        rol = obtener_rol_activo(request) # Lee el rol y lo guarda
        if view.action == 'deshabilitar':
            return es_gestor(request)
        if view.action in ('list', 'retrieve'): # Consultar la lista o el detalle se permite a cualquier rol valido
            return rol is not None
        if view.action in ('revisores', 'evaluar'): # Asignar/consultar revisores y evaluar queda solo para el comite
            return rol == 'comite'
        return rol == 'autor'
