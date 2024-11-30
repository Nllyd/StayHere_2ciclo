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
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from .serializers import UsuarioSerializer, AlojamientoSerializer, ImagenAlojamientoSerializer
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate, login
from datetime import datetime
from .models import Usuario
import random
import string
from io import BytesIO
from django.http import HttpResponse
from PIL import Image, ImageDraw, ImageFont
from django.core.cache import cache
from django.conf import settings

def logout_view(request):
    logout(request)
    return redirect('home')

def landing_view(request):
    return render(request, 'myapp/landing.html')

def alert_view(request):
    return render(request, 'myapp/alert.html')

def home_view(request):
    alojamientos = Alojamiento.objects.all()
    
    coordenadas = [
        {
            'latitud': alojamiento.latitud,
            'longitud': alojamiento.longitud,
            'id': alojamiento.id,
            'distrito': alojamiento.distrito
        } for alojamiento in alojamientos
    ]
    
    context = {
        'alojamientos': alojamientos,
        'coordenadas_json': json.dumps(coordenadas)
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
        user_captcha = request.POST['captcha']
        
        # Verificar el captcha almacenado en caché
        captcha_stored = cache.get(request.session.session_key)
        if user_captcha != captcha_stored:
            return JsonResponse({'success': False, 'error': 'Captcha incorrecto'})

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logueo exitoso')
            
            if user.is_superuser:
                return JsonResponse({'success': True, 'redirect': '/admin_users'})
        
            # Verifica el tipo de usuario y el estado de verificación
            # Verificar el tipo de usuario y redirigir adecuadamente
            if user.tipo_usuario.lower() == 'estudiante':
                if user.is_verified:
                    return JsonResponse({'success': True, 'redirect': '/home'})
                else:
                    return JsonResponse({'success': True, 'redirect': '', 'show_verification_modal': True})  # Redirigir a la página de mensaje si no está verificado

            elif user.tipo_usuario.lower() == 'arrendador':
                if user.is_verified:
                    return JsonResponse({'success': True, 'redirect': '/home'})  # Redirigir a home si es arrendador y verificado
                else:
                    return JsonResponse({'success': False, 'redirect': '/arrendador_verification_message'})  # Redirigir a la página de mensaje si no está verificado

        else:
            return JsonResponse({'success': False, 'error': 'Correo o contraseña incorrectos'})

    return render(request, 'myapp/login.html')

@login_required
def nuevo_view(request):
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        distrito = request.POST.get('distrito')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        caracteristicas = request.POST.getlist('caracteristicas')
        imagenes = request.FILES.getlist('imagenes')

        if not descripcion or not precio or not distrito:
            messages.error(request, 'Por favor, completa todos los campos requeridos.')
            return render(request, 'myapp/nuevo.html')

        if not latitud or not longitud:
            messages.error(request, 'Por favor, selecciona una ubicación en el mapa.')
            return render(request, 'myapp/nuevo.html')

        try:
            alojamiento = Alojamiento.objects.create(
                descripcion=descripcion,
                precio=precio,
                distrito=distrito,
                latitud=float(latitud),
                longitud=float(longitud),
                caracteristicas=caracteristicas,
                usuario=request.user
            )
        except ValueError:
            messages.error(request, 'Latitud y longitud deben ser números válidos.')
            return render(request, 'myapp/nuevo.html')

        for imagen in imagenes:
            ImagenAlojamiento.objects.create(alojamiento=alojamiento, imagen=imagen)

        messages.success(request, 'Alojamiento guardado exitosamente.')
        return redirect('home')
    
    return render(request, 'myapp/nuevo.html')

from django.core.mail import send_mail
from django.conf import settings

def register_view(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        telefono = request.POST['telefono']
        password = request.POST['password']
        captcha_user_input = request.POST['captcha']
        fecha_nacimiento_str = request.POST['fecha_nacimiento']
        
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
        except ValueError:
            return render(request, 'myapp/register.html', {'error': 'Formato de fecha incorrecto. Usa AAAA-MM-DD'})

        dni = request.POST.get('dni', None)
        tipo_usuario = request.POST['tipo_usuario']  # Captura el tipo de usuario

        if tipo_usuario == 'estudiante':
            student_email_prefix = request.POST['student_email_prefix']
            student_email_domain = request.POST['student_email_domain']
            email = student_email_prefix + student_email_domain
        else:  # Para arrendador
            email = request.POST.get('arrendador_email')

        captcha_stored = cache.get(request.session.session_key)

        if not captcha_stored or captcha_user_input.upper() != captcha_stored:
            return render(request, 'myapp/register.html', {'error': 'Captcha incorrecto'})

        if Usuario.objects.filter(email=email).exists():
            return render(request, 'myapp/register.html', {'error': 'Correo ya utilizado'})

        try:
            # Crear el usuario usando la fecha de nacimiento ya convertida
            usuario = Usuario.objects.create_user(
                nombre=nombre,
                email=email,
                telefono=telefono,
                fecha_nacimiento=fecha_nacimiento,
                dni=dni,
                tipo_usuario=tipo_usuario,  # Agregar el tipo de usuario
                password=password
            )
            usuario.save()
            
            # Enviar el código de verificación solo si es estudiante
            if tipo_usuario == 'estudiante':
                verification_code = generate_verification_code()
                send_mail(
                    'Código de Verificación',
                    f'Tu código de verificación es: {verification_code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

                # Guardar el código en el usuario para validación posterior
                usuario.verification_code = verification_code
                usuario.is_verified = False  # Asegúrate de tener este campo en tu modelo
                usuario.save()

                messages.success(request, 'Registro exitoso. Por favor, verifica tu correo electrónico.')
                return JsonResponse({'success': True, 'redirect': '/login'})  # Redirigir a /login
            else:
                # Para arrendadores, solo guardamos el usuario sin enviar el correo
                usuario.is_verified = False
                usuario.save()
                messages.success(request, 'Registro exitoso. Tus datos deben ser verificados. Se te enviará un correo cuando puedas ingresar.')
                return redirect('arrendador_verification_message')  # Redirigir a la página con el mensaje para arrendadores

        except IntegrityError:
            return render(request, 'myapp/register.html', {'error': 'Error al crear el usuario'})

    captcha_text = generate_captcha(request)
    return render(request, 'myapp/register.html', {'captcha': captcha_text})


@login_required
def user_view(request):
    usuario = request.user
    alojamientos = Alojamiento.objects.filter(usuario=usuario)

    if request.method == 'POST':
        # Validación de datos
        telefono = request.POST.get('telefono')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')

        if not telefono or not fecha_nacimiento:
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'myapp/user.html', {'usuario': usuario, 'alojamientos': alojamientos})

        usuario.telefono = telefono
        usuario.fecha_nacimiento = fecha_nacimiento

        # Actualizar valores de los checkboxes
        usuario.mostrar_whatsapp = 'mostrar_whatsapp' in request.POST
        usuario.mostrar_tiktok = 'mostrar_tiktok' in request.POST
        usuario.mostrar_instagram = 'mostrar_instagram' in request.POST
        usuario.mostrar_facebook = 'mostrar_facebook' in request.POST

        # Actualizar URL de redes sociales
        usuario.tiktok_url = request.POST.get('tiktok_url', '')
        usuario.instagram_url = request.POST.get('instagram_url', '')
        usuario.facebook_url = request.POST.get('facebook_url', '')

        # Actualizar la foto de perfil si se ha subido una nueva
        if 'foto_perfil' in request.FILES:
            usuario.foto_perfil = request.FILES['foto_perfil']

        usuario.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
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

@login_required
def editar_alojamiento_view(request, alojamiento_id):
    alojamiento = get_object_or_404(Alojamiento, id=alojamiento_id, usuario=request.user)

    if request.method == 'POST':
        alojamiento_id = request.POST['alojamiento_id']
        alojamiento = Alojamiento.objects.get(id=alojamiento_id)

        alojamiento.nombre = request.POST['nombre']
        alojamiento.descripcion = request.POST['descripcion']
        alojamiento.precio = request.POST['precio']
        alojamiento.latitud = request.POST['latitud']
        alojamiento.longitud = request.POST['longitud']
        alojamiento.caracteristicas = request.POST['caracteristicas'].split(', ')
        alojamiento.save()

        messages.success(request, 'Alojamiento actualizado exitosamente.')
        
        return JsonResponse({'status': 'success'})

    return render(request, 'myapp/editar_alojamiento.html', {'alojamiento': alojamiento})



# --------------------------- CODIGOS DE VALIDACION ---------------------------
@csrf_exempt
def verification_code_view(request):
    # Asegúrate de que el usuario esté autenticado
    if request.user.is_authenticated:
        if request.method == 'POST':
            code_entered = request.POST.get('verification_code')
            if code_entered == request.user.verification_code:
                request.user.is_verified = True
                request.user.save()
                messages.success(request, 'Correo verificado exitosamente.')
                return JsonResponse({'success': True})  # Retornar éxito si la verificación es correcta
            else:
                return JsonResponse({'success': False, 'error': 'Código de verificación incorrecto.'})

    return JsonResponse({'success': False, 'error': 'Usuario no autenticado.'})

def arrendador_verification_message_view(request):
    return render(request, 'myapp/arrendador_verification_message.html')

def generate_verification_code(length=8):
    characters = string.ascii_letters + string.digits  # Letras y números
    return ''.join(random.choice(characters) for _ in range(length))

def generate_captcha(request):
    captcha_text = ''.join(random.choices(string.ascii_uppercase, k=4))

    # Guarda el texto del captcha en el caché con una caducidad de 300 segundos
    cache.set(request.session.session_key, captcha_text, 300)

    # Configuración de la imagen del captcha
    width, height = 150, 50
    image = Image.new('RGB', (width, height), color=(255, 255, 255))

    # Cargar la fuente con la ruta absoluta para diagnóstico
    font = ImageFont.truetype("DejaVuSans.ttf", 36)
    
    # Dibujar el texto en la imagen
    draw = ImageDraw.Draw(image)
    draw.text((10, 5), captcha_text, font=font, fill=(0, 0, 0))

    # Añadir líneas aleatorias para hacer el captcha más complejo
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line(((x1, y1), (x2, y2)), fill=(0, 0, 0), width=2)

    # Guardar la imagen en un buffer en formato PNG
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)

    # Retornar la imagen como respuesta HTTP
    return HttpResponse(buffer, content_type='image/png')
    
@csrf_exempt
def validar_rechazar_usuario(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        usuario_id = data.get('id')
        accion = data.get('accion')

        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            # Verificar si la acción es de validación
            if accion == 'validar':
                usuario.is_verified = True
                usuario.is_active = True  # Asegúrate de activar el usuario si es necesario
                usuario.save()
                
                # Enviar correo de aceptación
                send_mail(
                    'Validación Exitosa',
                    f'Estimado {usuario.nombre},\n\n'
                    'Nos complace informarle que su cuenta ha sido verificada exitosamente. '
                    'Ahora tiene acceso completo a nuestra plataforma.\n\n'
                    'Saludos,\nEquipo de Soporte',
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.email],
                    fail_silently=False,
                )
                
                return JsonResponse({'status': 'success', 'message': 'Usuario verificado correctamente.'})
            
            # Verificar si la acción es de rechazo
            elif accion == 'rechazar':
                usuario.is_verified = False
                usuario.is_active = False  # Marcar como inactivo si es rechazado
                usuario.save()
                
                # Enviar correo de rechazo
                send_mail(
                    'Cuenta No Verificada',
                    f'Estimado {usuario.nombre},\n\n'
                    'Lamentamos informarle que su cuenta no cumple con los requisitos de verificación '
                    'y no ha sido aprobada. Si tiene alguna consulta o desea más información, por favor '
                    'contáctenos a través de nuestro soporte.\n\n'
                    'Atentamente,\nEquipo de Soporte',
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.email],
                    fail_silently=False,
                )
                
                return JsonResponse({'status': 'success', 'message': 'Usuario no verificado y marcado como inactivo.'})
            
            # En caso de una acción desconocida
            else:
                return JsonResponse({'status': 'error', 'message': 'Acción no reconocida.'}, status=400)

        except Usuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Usuario no encontrado.'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

# --------------------------- ADMINISTRADOR ---------------------------

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

        if not request.user.admin_permissions.can_edit_users:
            return HttpResponseForbidden("No tienes permiso para editar usuarios.")

        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        is_admin = request.POST.get('is_admin') == 'true'
        is_active = request.POST.get('is_active') == 'true'
        tipo_usuario = request.POST.get('tipo_usuario')

        try:
            usuario = Usuario.objects.get(id=usuario_id)
            usuario.nombre = nombre
            usuario.email = email
            usuario.telefono = telefono
            usuario.is_active = is_active

            if fecha_nacimiento:
                try:
                    usuario.fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Formato de fecha inválido. Usa el formato AAAA-MM-DD'}, status=400)

            usuario.tipo_usuario = tipo_usuario
            if request.user.admin_permissions.can_grant_permissions:
                usuario.is_superuser = is_admin

            usuario.save()
            return JsonResponse({'status': 'success', 'message': 'Usuario actualizado correctamente'})

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

    arrendadores_no_verificados = Usuario.objects.filter(tipo_usuario='Arrendador', is_verified=False)

    context = {
        'labels': json.dumps(labels),
        'data': json.dumps(data),
        'arrendadores_no_verificados': arrendadores_no_verificados,
    }

    return render(request, 'myapp/admin_control.html', context)

@superuser_required
def admin_permisos(request):
    administradores = Usuario.objects.filter(is_superuser=True).select_related('admin_permissions')
    context = {
        'administradores': administradores
    }
    return render(request, 'myapp/admin_permisos.html', context)



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

def update_permission(request, admin_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_permission = AdminPermissions.objects.get(usuario_id=admin_id)

            # Iterar sobre los datos y actualizar los atributos de permisos
            for key, value in data.items():
                if hasattr(admin_permission, key):
                    setattr(admin_permission, key, value)

            admin_permission.save()
            return JsonResponse({'success': True, 'message': 'Permiso actualizado exitosamente'})
        except AdminPermissions.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Administrador no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})



# --------------------------- HTTP PARA FLUTTER ---------------------------

@api_view(['GET'])
def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})

@csrf_exempt
@api_view(['POST'])
def create_usuario(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')
    nombre = data.get('nombre')
    telefono = data.get('telefono')
    tipo_usuario = data.get('tipo_usuario')
    fecha_nacimiento_str = data.get('fecha_nacimiento')

    if not email or not password or not nombre or not telefono or not fecha_nacimiento_str:
        return Response({'error': 'Todos los campos son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()  # Formato 'YYYY-MM-DD'
    except ValueError:
        return Response({'error': 'Formato de fecha inválido. Usa el formato AAAA-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    if Usuario.objects.filter(email=email).exists():
        return Response({'error': 'El correo ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuario.objects.create_user(
            email=email,
            nombre=nombre,
            telefono=telefono,
            fecha_nacimiento=fecha_nacimiento,
            password=password
        )
        usuario.save()
        return Response({'message': 'Usuario creado exitosamente'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@csrf_exempt
@api_view(['POST'])
def login_usuario(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'success': False, 'message': 'Email y contraseña son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=email, password=password)

    if user is not None:
        login(request, user)
        csrf_token = get_token(request)
        response = Response({'success': True, 'message': 'Inicio de sesión exitoso'})
        response.set_cookie('csrftoken', csrf_token)
        return response
    else:
        return Response({'success': False, 'message': 'Credenciales incorrectas'}, status=status.HTTP_400_BAD_REQUEST)

    


class UsuarioDetailByEmail(APIView):
    permission_classes = [IsAuthenticated]  # Asegúrate de que el usuario esté autenticado

    def get(self, request, email, format=None):
        try:
            usuario = Usuario.objects.get(email=email)  # Buscar al usuario por email
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)
        
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
