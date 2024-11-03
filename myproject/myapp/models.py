from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from datetime import date

class MyUserManager(BaseUserManager):
    def create_user(self, email, nombre, telefono, tipo_usuario, fecha_nacimiento=None, password=None, dni=None):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nombre=nombre,
            telefono=telefono,
            tipo_usuario=tipo_usuario,
            fecha_nacimiento=fecha_nacimiento,
            dni=dni,
            username=email  # Usamos el email como username
        )
        
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nombre, telefono, fecha_nacimiento=None, password=None, dni=None):
        user = self.create_user(
            email=email,
            nombre=nombre,
            telefono=telefono,
            tipo_usuario='Administrador',  # Tipo de usuario en mayúscula inicial
            fecha_nacimiento=fecha_nacimiento,
            password=password,
            dni=dni,
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class Usuario(AbstractUser):
    TIPOS_USUARIO = [
        ('Estudiante', 'Estudiante'),
        ('Administrador', 'Administrador'),
        ('Arrendador', 'Arrendador'),
    ]

    # Campos personalizados
    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    mostrar_whatsapp = models.BooleanField(default=False)
    tipo_usuario = models.CharField(max_length=20, choices=TIPOS_USUARIO, default='Estudiante')
    dni = models.CharField(max_length=8, null=True, blank=True)
    verification_code = models.CharField(max_length=8, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'telefono', 'fecha_nacimiento', 'tipo_usuario']

    def __str__(self):
        return f"{self.email} - {self.get_tipo_usuario_display()}"

    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None

    def save(self, *args, **kwargs):
    # Si el usuario es superusuario, aseguramos que el tipo de usuario sea "Administrador"
        if self.is_superuser:
            self.tipo_usuario = 'Administrador'
        else:
            # Si el usuario no es superusuario y el tipo actual es "Administrador", restauramos su tipo original
            if self._state.adding is False and Usuario.objects.filter(pk=self.pk).exists():
                original_tipo = Usuario.objects.get(pk=self.pk).tipo_usuario
                # Cambiar a "Estudiante" solo si el tipo original era "Administrador"
                if self.tipo_usuario == 'Administrador':
                    self.tipo_usuario = original_tipo if original_tipo != 'Administrador' else 'Estudiante'

        super().save(*args, **kwargs)


class Alojamiento(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    latitud = models.FloatField()
    longitud = models.FloatField()
    caracteristicas = models.JSONField()

    def __str__(self):
        return self.nombre

class ImagenAlojamiento(models.Model):
    alojamiento = models.ForeignKey(Alojamiento, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='alojamientos/')

    def __str__(self):
        return f"Imagen de {self.alojamiento.nombre}"

class AdminPermissions(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='admin_permissions')
    can_edit_users = models.BooleanField(default=False)
    can_delete_users = models.BooleanField(default=False)
    can_edit_alojamientos = models.BooleanField(default=False)
    can_delete_alojamientos = models.BooleanField(default=False)
    can_grant_permissions = models.BooleanField(default=False)

    def __str__(self):
        return f"Permisos de {self.usuario.email}"
