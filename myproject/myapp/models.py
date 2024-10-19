from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from datetime import date

class MyUserManager(BaseUserManager):
    def create_user(self, email, nombre, telefono, fecha_nacimiento=None, password=None):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        
        if fecha_nacimiento:
            today = date.today()
            edad = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        else:
            edad = None

        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, telefono=telefono, fecha_nacimiento=fecha_nacimiento, username=email)
        
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nombre, telefono, fecha_nacimiento=None, password=None):
        user = self.create_user(email=email, nombre=nombre, telefono=telefono, fecha_nacimiento=fecha_nacimiento, password=password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Usuario(AbstractUser):
    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField(null=True, blank=True)  # Cambiar de edad a fecha de nacimiento
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    mostrar_whatsapp = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'telefono', 'fecha_nacimiento']  # Actualizar los campos requeridos

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions'
    )

    def __str__(self):
        return self.email

    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None


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
