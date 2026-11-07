from rest_framework import serializers

from .models import Evento


class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = ['id', 'nombre', 'fecha_inicio', 'fecha_fin', 'agenda_publicada', 'activo', 'postulacion_abierta', 'creado', 'actualizado']
        read_only_fields = ['agenda_publicada', 'activo', 'creado', 'actualizado']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_fin = attrs.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        if fecha_fin < fecha_inicio:
            raise serializers.ValidationError({'fecha_fin': 'La fecha de fin no puede ser anterior a la de inicio.'})
        return attrs



class FechasLimiteSerializer(serializers.Serializer):
    postulacion = serializers.DateTimeField()
    revision = serializers.DateTimeField()
    version_corregida = serializers.DateTimeField()
    version_final = serializers.DateTimeField()

    def validate(self, attrs):
        etapas = [
            ('postulacion', 'Postulación'),
            ('revision', 'Revisión'),
            ('version_corregida', 'Versión corregida'),
            ('version_final', 'Versión final'),
        ]
        for (anterior, texto_anterior), (siguiente, _) in zip(etapas, etapas[1:]):
            if attrs[siguiente] <= attrs[anterior]:
                raise serializers.ValidationError({siguiente: f'Debe ser posterior a {texto_anterior}.'})
        return attrs
