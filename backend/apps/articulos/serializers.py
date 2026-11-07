from django.db import transaction
from rest_framework import serializers
from .models import Articulo, Autor



class CoautorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['nombre', 'afiliacion', 'correo']


class ArticuloSerializer(serializers.ModelSerializer):
    afiliacion = serializers.CharField(max_length=200, write_only=True) # Campo adicional para capturar la afiliación del autor responsable al crear un artículo
    coautores = CoautorSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Articulo
        fields = ['id', 'evento', 'titulo', 'resumen', 'palabras_clave', 'linea_tematica', 'afiliacion', 'coautores', 'estado', 'creado']
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
