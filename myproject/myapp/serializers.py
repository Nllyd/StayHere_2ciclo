from rest_framework import serializers
from .models import Usuario, Alojamiento, ImagenAlojamiento

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # Hacer que la contraseña sea solo de escritura

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre', 'telefono', 'fecha_nacimiento', 'tipo_usuario', 'foto_perfil','edad', 'password']

    edad = serializers.ReadOnlyField()

    def create(self, validated_data):
        password = validated_data.pop('password')  # Obtener la contraseña
        validated_data['password'] = make_password(password)  # Cifrar la contraseña
        return super().create(validated_data)

        def update(self, instance, validated_data):
        # Si hay un campo de contraseña, lo ciframos
        if 'password' in validated_data:
            instance.password = make_password(validated_data.pop('password'))
        # Actualizamos los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class AlojamientoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    primera_imagen = serializers.SerializerMethodField()

    class Meta:
        model = Alojamiento
        fields = ['id', 'usuario', 'descripcion', 'precio', 'latitud', 'longitud', 'caracteristicas', 'primera_imagen']

    def get_primera_imagen(self, obj):
        primera_imagen = obj.imagenes.first()
        if primera_imagen:
            return primera_imagen.imagen.url
        return None

class ImagenAlojamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenAlojamiento
        fields = ['id', 'alojamiento', 'imagen']
