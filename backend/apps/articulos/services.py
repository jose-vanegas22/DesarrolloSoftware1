from django.db import transaction

from .models import Articulo, Revision, VersionArticulo  # Revision: pendiente de HU-17

TOTAL_EVALUACIONES = 3
VOTOS_PARA_DECIDIR = 2


@transaction.atomic  # Decorador para garantizar la atomicidad en la base de datos
def calcular_resultado(articulo):
    # Solo se calcula una vez, mientras el articulo esta en revision
    if articulo.estado != Articulo.Estado.EN_REVISION:
        return None

    # Solo cuentan las evaluaciones de la version inicial
    evaluaciones = Revision.objects.filter(
        version__articulo=articulo,
        version__tipo=VersionArticulo.Tipo.INICIAL,
    )
    if evaluaciones.count() < TOTAL_EVALUACIONES:
        return None

    aceptan = evaluaciones.filter(decision=Revision.Decision.ACEPTAR).count()
    rechazan = evaluaciones.filter(decision=Revision.Decision.RECHAZAR).count()

    if aceptan >= VOTOS_PARA_DECIDIR:
        articulo.estado = Articulo.Estado.ACEPTADO
    elif rechazan >= VOTOS_PARA_DECIDIR:
        articulo.estado = Articulo.Estado.RECHAZADO
    else:
        return None

    articulo.save(update_fields=['estado', 'actualizado'])
    return articulo.estado


# Usada para los test
# Regla de negocio pura: recibe conteos y devuelve el estado resultante, o None si aun no se decide
def resultado_por_votos(aceptan, rechazan, total):
    if total < TOTAL_EVALUACIONES:
        return None
    if aceptan >= VOTOS_PARA_DECIDIR:
        return Articulo.Estado.ACEPTADO
    if rechazan >= VOTOS_PARA_DECIDIR:
        return Articulo.Estado.RECHAZADO
    return None