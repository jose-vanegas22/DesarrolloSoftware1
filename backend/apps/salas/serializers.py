from rest_framework import serializers

from .models import Sala


class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = ['id', 'nombre', 'capacidad', 'activo']
        read_only_fields = ['activo']
