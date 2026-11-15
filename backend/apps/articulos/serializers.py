from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from apps.eventos.models import FechaLimite
from apps.usuarios.models import Usuario
from .models import MAX_ARTICULOS_POR_REVISOR, Articulo, AsignacionRevision, Autor, VersionArticulo, Revision
from .services import validar_revisor, validar_plazo_revision
from rest_framework.exceptions import APIException
from drf_spectacular.utils import extend_schema_field

class CoautorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['id', 'nombre', 'afiliacion', 'correo']


class AsignacionRevisionSerializer(serializers.ModelSerializer):
    revisor_nombre = serializers.CharField(source='revisor.nombres', read_only=True)
    revisor_apellidos = serializers.CharField(source='revisor.apellidos', read_only=True)
    revisor_correo = serializers.EmailField(source='revisor.correo', read_only=True)

    class Meta:
        model = AsignacionRevision
        fields = ['id', 'revisor', 'revisor_nombre', 'revisor_apellidos', 'revisor_correo', 'creado']
        read_only_fields = fields


class AsignarRevisoresSerializer(serializers.Serializer):
    revisores = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), many=True)

    def validate_revisores(self, revisores):
        articulo = self.context['articulo']

        fecha_postulacion = articulo.evento.fechas_limite.filter(etapa=FechaLimite.Etapa.POSTULACION).first()
        if fecha_postulacion is None:
            raise serializers.ValidationError('El evento no tiene configurada la fecha limite de postulacion.')
        if timezone.now() <= fecha_postulacion.fecha:
            raise serializers.ValidationError('La postulacion aun no ha terminado.')

        if len(revisores) != 3:
            raise serializers.ValidationError('Se deben asignar exactamente tres revisores.')

        ids = [revisor.id for revisor in revisores]
        if len(set(ids)) != 3:
            raise serializers.ValidationError('Los tres revisores deben ser diferentes.')

        correos_autores = {articulo.autor_responsable.correo.lower().strip()}
        correos_autores.update(autor.correo.lower().strip() for autor in articulo.autores.all())

        for revisor in revisores:
            if not revisor.es_comite:
                raise serializers.ValidationError(
                    f'{revisor} no pertenece al comite cientifico.'
                )
            if revisor.id == articulo.autor_responsable_id or revisor.correo.lower().strip() in correos_autores:
                raise serializers.ValidationError(
                    f'{revisor} es autor o coautor del articulo y no puede revisarlo.'
                )
            if articulo.linea_tematica not in (revisor.especialidades or []):
                raise serializers.ValidationError(
                    f'{revisor} no tiene experiencia en la linea tematica del articulo.'
                )
            asignados = AsignacionRevision.objects.filter(revisor=revisor).exclude(articulo=articulo).count()
            if asignados >= MAX_ARTICULOS_POR_REVISOR:
                raise serializers.ValidationError(
                    f'{revisor} ya tiene el maximo de {MAX_ARTICULOS_POR_REVISOR} articulos asignados.'
                )

        return revisores


class ArticuloSerializer(serializers.ModelSerializer):
    afiliacion = serializers.CharField(max_length=200, write_only=True) # Campo adicional para capturar la afiliación del autor responsable al crear un artículo
    coautores = CoautorSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Articulo
        fields = ['id', 'evento', 'evento_nombre', 'titulo', 'resumen', 'palabras_clave', 'linea_tematica', 'linea_tematica_nombre', 'afiliacion', 'coautores', 'estado', 'estado_nombre', 'creado']
        read_only_fields = ['estado', 'creado'] # Evita que el estado y la fecha de creación sean modificables por el usuario

    # Nos permite rechazar el evento si esta inactiva, si no tiene fecha de postulacion configurada o si ya vencio
    def validate_evento(self, evento):
        if not evento.postulacion_abierta:
            raise serializers.ValidationError('La postulación de esta conferencia no está abierta.')
        return evento

    def validate_coautores(self, coautores):
        correos = {self.context['request'].user.correo.lower()}
        for coautor in coautores:
            correo = coautor['correo'].lower()
            if correo in correos:
                raise serializers.ValidationError('No puedes repetir el correo de un autor.')
            correos.add(correo)
        return coautores

    evento_nombre = serializers.CharField(source='evento.nombre', read_only=True) # Permite mostrar el nombre del evento en la respuesta del serializer, sin necesidad de hacer otra consulta a la base de datos.
    linea_tematica_nombre = serializers.CharField(source='get_linea_tematica_display', read_only=True)
    estado_nombre = serializers.CharField(source='get_estado_display', read_only=True)
    

    # Guarda el articulo y al autor responsable
    @transaction.atomic # Agrupa las operaciones en una sola transaccion, si falla el registro del autor responsable tambien el del articulo
    def create(self, validated_data):
        afiliacion = validated_data.pop('afiliacion') # Saca afiliacion para que no se guarde en articulo porque no tiene ese campo en su tabla
        coautores = validated_data.pop('coautores', [])
        usuario = self.context['request'].user # Obtiene el usuario autenticado por JWT

        articulo = Articulo.objects.create(autor_responsable=usuario, **validated_data) # Crea la fila en la tabla articulo
        Autor.objects.create(
            articulo=articulo,
            nombre=f'{usuario.nombres} {usuario.apellidos}',
            afiliacion=afiliacion,
            correo=usuario.correo,
        )
        for coautor in coautores:
            Autor.objects.create(articulo=articulo, **coautor)

        return articulo



class ArticuloDetalleSerializer(ArticuloSerializer):
    autores = serializers.SerializerMethodField()
    fecha_pdf = serializers.SerializerMethodField()
    postulacion_abierta = serializers.BooleanField(source='evento.postulacion_abierta', read_only=True)
    pdf_url = serializers.SerializerMethodField()
    evaluacion = serializers.SerializerMethodField()


    class Meta(ArticuloSerializer.Meta):
        fields = ArticuloSerializer.Meta.fields + ['autores', 'fecha_pdf', 'postulacion_abierta', 'pdf_url', 'evaluacion']

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_pdf_url(self, articulo):
        version = articulo.versiones.filter(tipo=VersionArticulo.Tipo.INICIAL).order_by('-creado', '-pk').first()
        return version.archivo.url if version and version.archivo else None

    @extend_schema_field(serializers.DictField())
    def get_evaluacion(self, articulo):
        # Solo se expone la evaluación propia; no las decisiones de otros revisores.
        try:
            asignacion = validar_revisor(self.context['request'], articulo)
            revision = Revision.objects.filter(asignacion=asignacion).first()
            if revision:
                return {'puede_evaluar': False, 'motivo': 'Ya registraste tu evaluación.', 'revision': RevisionSerializer(revision).data}
            validar_plazo_revision(articulo)
        except APIException as error:
            return {'puede_evaluar': False, 'motivo': str(error.detail), 'revision': None}
        return {'puede_evaluar': True, 'motivo': '', 'revision': None}

    @extend_schema_field(CoautorSerializer(many=True))
    def get_autores(self, articulo):
        return CoautorSerializer(articulo.autores.order_by('id'), many=True).data

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_fecha_pdf(self, articulo):
        version = articulo.versiones.filter(tipo=VersionArticulo.Tipo.INICIAL).first()
        return serializers.DateTimeField().to_representation(version.creado) if version else None




# Se agrego para subir los PDF de los articulos, valida que sea PDF y que no supere el tamaño maximo
class VersionArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionArticulo
        fields = ['id', 'tipo', 'archivo', 'creado']
        read_only_fields = ['tipo', 'creado']
        extra_kwargs = {'archivo': {'write_only': True}}

    def validate_archivo(self, archivo):
        if archivo.size > settings.TAMANO_MAXIMO_PDF_MB * 1024 * 1024:
            raise serializers.ValidationError(f'El PDF no puede superar {settings.TAMANO_MAXIMO_PDF_MB} MB.')

        archivo.seek(0)
        es_pdf = archivo.name.lower().endswith('.pdf') and archivo.read(5) == b'%PDF-'
        archivo.seek(0)
        if not es_pdf:
            raise serializers.ValidationError('Solo se permiten archivos PDF.')
        return archivo

    def validate(self, attrs):
        articulo = self.context['articulo']
        if not articulo.evento.postulacion_abierta:
            raise serializers.ValidationError('La postulación de esta conferencia no está abierta.')
        if articulo.versiones.filter(tipo=VersionArticulo.Tipo.INICIAL).exists():
            raise serializers.ValidationError('Este artículo ya tiene un PDF inicial.')
        return attrs


class RevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revision
        fields = ['id', 'decision', 'comentarios', 'creado']
        read_only_fields = ['id', 'creado']

