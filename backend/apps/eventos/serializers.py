from rest_framework import serializers

from .models import Evento


class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = ['id', 'nombre', 'fecha_inicio', 'fecha_fin', 'agenda_publicada', 'activo', 'creado', 'actualizado']
        read_only_fields = ['agenda_publicada', 'activo', 'creado', 'actualizado']

    def validate(self, attrs):
        fecha_inicio = attrs.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_fin = attrs.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        if fecha_fin < fecha_inicio:
            raise serializers.ValidationError({'fecha_fin': 'La fecha de fin no puede ser igual a la de inicio.'})
        return attrs
