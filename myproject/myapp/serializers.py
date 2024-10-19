from rest_framework import serializers
from .models import Usuario, Alojamiento, ImagenAlojamiento

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre', 'telefono', 'fecha_nacimiento']

    edad = serializers.ReadOnlyField()

class AlojamientoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Alojamiento
        fields = ['id', 'usuario', 'nombre', 'descripcion', 'precio', 'latitud', 'longitud', 'caracteristicas']

class ImagenAlojamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenAlojamiento
        fields = ['id', 'alojamiento', 'imagen']
