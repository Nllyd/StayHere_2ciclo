from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from .models import Usuario, Alojamiento, ImagenAlojamiento, AdminPermissions
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Count
from django.db.models.functions import TruncMonth

from rest_framework import generics
from .serializers import UsuarioSerializer, AlojamientoSerializer, ImagenAlojamientoSerializer


import random
import string
from io import BytesIO
from django.http import HttpResponse
from PIL import Image, ImageDraw, ImageFont
from django.core.cache import cache

def logout_view(request):
    logout(request)
    return redirect('home')

def landing_view(request):
    return render(request, 'myapp/landing.html')

def alert_view(request):
    return render(request, 'myapp/alert.html')

def home_view(request):
    # Obtener todos los alojamientos
    alojamientos = Alojamiento.objects.all()
    
    # Crear una lista de diccionarios con la información necesaria
    coordenadas = [
        {
            'latitud': alojamiento.latitud,
            'longitud': alojamiento.longitud,
            'nombre': alojamiento.nombre,
            'id': alojamiento.id
        } for alojamiento in alojamientos
    ]
    
    # Pasar la lista de coordenadas al contexto y asegurarse de que se renderice como JSON en el template
    context = {
        'alojamientos': alojamientos,
        'coordenadas_json': json.dumps(coordenadas)  # Convierte las coordenadas a JSON para pasarlas al frontend
    }
    
    return render(request, 'myapp/home.html', context)

@login_required
def alojamiento_detalle_view(request, alojamiento_id):
    alojamiento = get_object_or_404(Alojamiento, id=alojamiento_id)
    return render(request, 'myapp/habitaciones.html', {'alojamiento': alojamiento})

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user_captcha = request.POST['captcha']  # Captura el captcha que el usuario ingresó

        # Verificar el captcha almacenado en caché
        captcha_stored = cache.get(request.session.session_key)
        if user_captcha != captcha_stored:
            return render(request, 'myapp/login.html', {'error': 'Captcha incorrecto'})

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logueo exitoso')

            # Verifica si el usuario es superuser
            if user.is_superuser:
                return redirect('admin_users')  # Redirige a la vista de admin_users si es superuser
            else:
                return redirect('home')  # Redirige a home si no es superuser
        else:
            return render(request, 'myapp/login.html', {'error': 'Correo o contraseña incorrectos'})
    return render(request, 'myapp/login.html')

@login_required
def nuevo_view(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        descripcion = request.POST['descripcion']
        precio = request.POST['precio']
        latitud = request.POST['latitud']
        longitud = request.POST['longitud']
        caracteristicas = request.POST.getlist('caracteristicas')
        imagenes = request.FILES.getlist('imagenes')

        if not latitud or not longitud:
            messages.error(request, 'Por favor, selecciona una ubicación en el mapa.')
            return render(request, 'myapp/nuevo.html')

        alojamiento = Alojamiento(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            latitud=float(latitud),
            longitud=float(longitud),
            caracteristicas=caracteristicas,
            usuario=request.user
        )
        alojamiento.save()
        
        for imagen in imagenes:
            ImagenAlojamiento.objects.create(alojamiento=alojamiento, imagen=imagen)

        messages.success(request, 'Alojamiento guardado exitosamente.')
        return redirect('home')
    
    return render(request, 'myapp/nuevo.html')

def register_view(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        email = request.POST['email']
        telefono = request.POST['telefono']
        fecha_nacimiento = request.POST['fecha_nacimiento']  # Capturar la fecha de nacimiento
        password = request.POST['password']
        captcha_user_input = request.POST['captcha']

        captcha_stored = cache.get(request.session.session_key)

        if not captcha_stored or captcha_user_input.upper() != captcha_stored:
            return render(request, 'myapp/register.html', {'error': 'Captcha incorrecto'})

        if Usuario.objects.filter(email=email).exists():
            return render(request, 'myapp/register.html', {'error': 'Correo ya utilizado'})

        try:
            usuario = Usuario(nombre=nombre, email=email, telefono=telefono, fecha_nacimiento=fecha_nacimiento, username=email)
            usuario.set_password(password)
            usuario.save()

            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Registro y logueo exitoso.')
                return redirect('home')

        except IntegrityError:
            return render(request, 'myapp/register.html', {'error': 'Error al crear el usuario'})

    captcha_text = generate_captcha(request)
    return render(request, 'myapp/register.html', {'captcha': captcha_text})

@login_required
def user_view(request):
    usuario = request.user
    alojamientos = Alojamiento.objects.filter(usuario=usuario)
    
    if request.method == 'POST':
        usuario.nombre = request.POST['nombre']
        usuario.telefono = request.POST['telefono']
        usuario.edad = request.POST['edad']
        usuario.mostrar_whatsapp = 'mostrar_whatsapp' in request.POST
        
        if 'foto_perfil' in request.FILES:
            usuario.foto_perfil = request.FILES['foto_perfil']
        
        usuario.save()
        return redirect('user')

    return render(request, 'myapp/user.html', {'usuario': usuario, 'alojamientos': alojamientos})

@login_required
def user_profile_view(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    alojamientos = Alojamiento.objects.filter(usuario=usuario)
    return render(request, 'myapp/user_profile.html', {'usuario': usuario, 'alojamientos': alojamientos})

class HabitacionesView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request):
        alojamientos = Alojamiento.objects.all()
        return render(request, 'myapp/habitaciones.html', {'alojamientos': alojamientos})
    
@login_required
def arrendador_profile_view(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    alojamientos = Alojamiento.objects.filter(usuario=usuario)
    return render(request, 'myapp/arrendador_profile.html', {'usuario': usuario, 'alojamientos': alojamientos})

# ADMINISTRADOR

# Decorador para restringir acceso solo a superusuarios
def superuser_required(view_func):
    decorated_view_func = user_passes_test(lambda user: user.is_superuser)(view_func)
    return decorated_view_func

# Vistas Administrativas

@superuser_required
def admin_users_view(request):
    usuarios = Usuario.objects.all()
    context = {
        'usuarios': usuarios
    }
    return render(request, 'myapp/admin_users.html', context)

@superuser_required
def actualizar_usuario(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('id')

        # Verificar si el usuario tiene permiso para editar usuarios
        if not request.user.admin_permissions.can_edit_users:
            return HttpResponseForbidden("No tienes permiso para editar usuarios.")

        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        edad = request.POST.get('edad')

        try:
            usuario = Usuario.objects.get(id=usuario_id)
            usuario.nombre = nombre
            usuario.email = email
            usuario.telefono = telefono
            usuario.edad = edad
            usuario.save()
            return JsonResponse({'status': 'success', 'usuario': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'telefono': usuario.telefono,
                'edad': usuario.edad
            }})
        except Usuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Usuario no encontrado.'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

@superuser_required
def eliminar_usuario(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('id')

        # Verificar si el usuario tiene permiso para eliminar usuarios
        if not request.user.admin_permissions.can_delete_users:
            return HttpResponseForbidden("No tienes permiso para eliminar usuarios.")

        try:
            usuario = Usuario.objects.get(id=usuario_id)
            usuario.delete()
            return JsonResponse({'status': 'success', 'message': 'Usuario eliminado correctamente.'})
        except Usuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Usuario no encontrado.'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

@superuser_required
def admin_habitaciones_view(request):
    alojamientos = Alojamiento.objects.all()
    context = {
        'alojamientos': alojamientos
    }
    return render(request, 'myapp/admin_habitaciones.html', context)

@superuser_required
def admin_control(request):
    registros_por_mes = (
        Usuario.objects.annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    labels = [registro['month'].strftime("%B") for registro in registros_por_mes]
    data = [registro['total'] for registro in registros_por_mes]

    context = {
        'labels': json.dumps(labels),
        'data': json.dumps(data),
    }

    return render(request, 'myapp/admin_control.html', context)

@superuser_required
def admin_permisos(request):
    administradores = Usuario.objects.filter(is_superuser=True).select_related('admin_permissions')
    context = {
        'administradores': administradores
    }
    return render(request, 'myapp/admin_permisos.html', context)


def generate_captcha(request):
    # Generar una cadena de 4 letras aleatorias
    captcha_text = ''.join(random.choices(string.ascii_uppercase, k=4))

    # Guardar el captcha en la sesión del usuario o en el caché
    cache.set(request.session.session_key, captcha_text, 300)  # Validez de 5 minutos

    # Crear la imagen del captcha
    width, height = 150, 50
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    font = ImageFont.truetype("arial.ttf", 36)  # Asegúrate de tener la fuente

    draw = ImageDraw.Draw(image)

    # Dibujar el texto del captcha
    draw.text((10, 5), captcha_text, font=font, fill=(0, 0, 0))

    # Añadir líneas sobre el captcha para hacer más difícil la lectura
    for _ in range(5):  # Dibujar 5 líneas
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line(((x1, y1), (x2, y2)), fill=(0, 0, 0), width=2)

    # Convertir la imagen a formato de bytes para devolverla como respuesta
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer, content_type='image/png')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Alojamiento

@superuser_required
def actualizar_alojamiento(request):
    if request.method == 'POST':
        alojamiento_id = request.POST.get('id')
        
        # Verificar si el usuario tiene permiso para editar alojamientos
        if not request.user.admin_permissions.can_edit_alojamientos:
            return HttpResponseForbidden("No tienes permiso para editar alojamientos.")
        
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')

        try:
            alojamiento = Alojamiento.objects.get(id=alojamiento_id)
            alojamiento.nombre = nombre
            alojamiento.descripcion = descripcion
            alojamiento.precio = precio
            alojamiento.latitud = latitud
            alojamiento.longitud = longitud
            alojamiento.save()
            return JsonResponse({'status': 'success'})
        except Alojamiento.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Alojamiento no encontrado'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@csrf_exempt
@superuser_required
def eliminar_alojamiento(request):
    if request.method == 'POST':
        alojamiento_id = request.POST.get('id')
        
        # Verificar si el usuario tiene permiso para eliminar alojamientos
        if not request.user.admin_permissions.can_delete_alojamientos:
            return HttpResponseForbidden("No tienes permiso para eliminar alojamientos.")

        try:
            alojamiento = Alojamiento.objects.get(id=alojamiento_id)
            alojamiento.delete()
            return JsonResponse({'status': 'success'})
        except Alojamiento.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Alojamiento no encontrado'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

#HTTP PARA FLUTTER

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['POST'])
def create_usuario(request):
    if request.method == 'POST':
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UsuarioListCreate(generics.ListCreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class UsuarioDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class AlojamientoListCreate(generics.ListCreateAPIView):
    queryset = Alojamiento.objects.all()
    serializer_class = AlojamientoSerializer

class AlojamientoDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alojamiento.objects.all()
    serializer_class = AlojamientoSerializer

class ImagenAlojamientoListCreate(generics.ListCreateAPIView):
    queryset = ImagenAlojamiento.objects.all()
    serializer_class = ImagenAlojamientoSerializer