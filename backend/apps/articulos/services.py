from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.eventos.models import FechaLimite
from apps.usuarios.permissions import obtener_rol_activo
from .models import Articulo, AsignacionRevision, Revision, VersionArticulo


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
    revision = Revision.objects.create(asignacion=asignacion, **datos)
    votos = Revision.objects.filter(asignacion__articulo=articulo)
    if votos.filter(decision=Revision.Decision.ACEPTAR).count() >= 2:
        articulo.estado = Articulo.Estado.ACEPTADO
    elif votos.filter(decision=Revision.Decision.RECHAZAR).count() >= 2:
        articulo.estado = Articulo.Estado.RECHAZADO
    else:
        articulo.estado = Articulo.Estado.EN_REVISION
    articulo.save(update_fields=['estado', 'actualizado'])
    return revision
