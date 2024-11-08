from rest_framework import serializers
from .models import Usuario, Alojamiento, ImagenAlojamiento

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre', 'telefono', 'fecha_nacimiento', 'edad']
    
    edad = serializers.ReadOnlyField()

class AlojamientoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    primera_imagen = serializers.SerializerMethodField()

    class Meta:
        model = Alojamiento
        fields = ['id', 'usuario', 'nombre', 'descripcion', 'precio', 'latitud', 'longitud', 'caracteristicas', 'primera_imagen']

    def get_primera_imagen(self, obj):
        primera_imagen = obj.imagenes.first()
        if primera_imagen:
            return primera_imagen.imagen.url
        return None

class ImagenAlojamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenAlojamiento
        fields = ['id', 'alojamiento', 'imagen']
