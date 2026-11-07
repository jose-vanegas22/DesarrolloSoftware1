from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.usuarios.permissions import es_gestor


class PermisoEventos(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or es_gestor(request)
