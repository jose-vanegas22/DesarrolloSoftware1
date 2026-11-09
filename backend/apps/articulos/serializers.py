from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from .models import Articulo, Autor, VersionArticulo
from drf_spectacular.utils import extend_schema_field

class CoautorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['nombre', 'afiliacion', 'correo']


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

    class Meta(ArticuloSerializer.Meta):
        fields = ArticuloSerializer.Meta.fields + ['autores', 'fecha_pdf']

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

