from rest_framework.permissions import SAFE_METHODS, BasePermission


def es_gestor(usuario):
    return usuario.es_administrador or usuario.es_comite

# Tiene 2 funciones porque el DRF revisa los permisos en dos momentos de la aplicacion
class PermisoUsuarios(BasePermission):
    # Una peticion primero pasa por aqui, GET, PUT, PATCH los deja pasar, POST, DELETE los bloquea si es autor
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS or request.method in ('PUT', 'PATCH'):
            return True
        return es_gestor(request.user)

    # Este segundo filtra segun a quien afecta la peticion, si es a otro usuario, solo los gestores pueden hacerlo, pero si eres autor y te quieres modificar tu mismo te deja
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or es_gestor(request.user):
            return True
        return request.method in ('PUT', 'PATCH') and obj == request.user
