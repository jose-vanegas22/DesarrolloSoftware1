from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.eventos.models import FechaLimite
from apps.usuarios.permissions import obtener_rol_activo
from .models import Articulo, AsignacionRevision, Revision, VersionArticulo


@transaction.atomic
def calcular_resultado(articulo):
    # Se bloquea la misma fila que al registrar votos, hasta terminar la transaccion.
    articulo = Articulo.objects.select_for_update().get(pk=articulo.pk, activo=True)
    if articulo.estado != Articulo.Estado.EN_REVISION:
        return None

    decisiones = list(Revision.objects.filter(
        asignacion__articulo=articulo,
    ).values_list('decision', flat=True))
    # Incluso dos votos iguales deben esperar la tercera evaluacion (HU-18).
    if len(decisiones) != 3:
        return None
    if any(decision not in Revision.Decision.values for decision in decisiones):
        raise ValidationError('Las evaluaciones contienen una decisión inválida.')

    articulo.estado = (
        Articulo.Estado.ACEPTADO
        if decisiones.count(Revision.Decision.ACEPTAR) >= 2
        else Articulo.Estado.RECHAZADO
    )
    articulo.save(update_fields=['estado', 'actualizado'])
    return articulo.estado


def validar_revisor(request, articulo):
    if obtener_rol_activo(request) != 'comite':
        raise PermissionDenied('Debes usar el rol de comité para evaluar.')
    asignacion = AsignacionRevision.objects.filter(articulo=articulo, revisor=request.user).first()
    if asignacion is None:
        raise PermissionDenied('No estás asignado como revisor de este artículo.')
    if articulo.autor_responsable_id == request.user.pk or articulo.autores.filter(correo__iexact=request.user.correo).exists():
        raise PermissionDenied('No puedes evaluar un artículo del que eres autor.')
    return asignacion


def validar_plazo_revision(articulo):
    fechas = dict(articulo.evento.fechas_limite.values_list('etapa', 'fecha'))
    ahora = timezone.now()
    cierre = fechas.get(FechaLimite.Etapa.POSTULACION)
    limite = fechas.get(FechaLimite.Etapa.REVISION)
    if not articulo.evento.activo or cierre is None or limite is None or not cierre < ahora <= limite:
        raise ValidationError('La conferencia no está dentro del plazo de revisión.')
    if articulo.estado not in (Articulo.Estado.POSTULADO, Articulo.Estado.EN_REVISION, Articulo.Estado.ACEPTADO, Articulo.Estado.RECHAZADO):
        raise ValidationError('El artículo no está en la etapa de evaluación inicial.')
    if not articulo.versiones.filter(tipo=VersionArticulo.Tipo.INICIAL).exists():
        raise ValidationError('El artículo no tiene PDF inicial para evaluar.')


@transaction.atomic
def registrar_revision(request, articulo, datos):
    # Serializa los votos del mismo artículo para calcular la mayoría sin perder votos concurrentes.
    articulo = Articulo.objects.select_for_update().select_related('evento').get(pk=articulo.pk, activo=True)
    asignacion = validar_revisor(request, articulo)
    if Revision.objects.filter(asignacion=asignacion).exists():
        raise ValidationError('Ya registraste una evaluación para este artículo.')
    validar_plazo_revision(articulo)
    if articulo.estado not in (Articulo.Estado.POSTULADO, Articulo.Estado.EN_REVISION):
        raise ValidationError('El artículo ya tiene un resultado de revisión.')
    if Revision.objects.filter(asignacion__articulo=articulo).count() >= 3:
        raise ValidationError('El artículo ya tiene las tres evaluaciones.')
    revision = Revision.objects.create(asignacion=asignacion, **datos)
    if articulo.estado == Articulo.Estado.POSTULADO:
        articulo.estado = Articulo.Estado.EN_REVISION
        articulo.save(update_fields=['estado', 'actualizado'])
    calcular_resultado(articulo)
    return revision
