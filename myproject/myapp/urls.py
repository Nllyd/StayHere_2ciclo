from django.urls import path
from . import views
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('home/', views.home_view, name='home'),
    path('alert/', views.alert_view, name='alert'),
    path('habitaciones/', views.HabitacionesView.as_view(), name='habitaciones'),
    path('nuevo/', views.nuevo_view, name='nuevo'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('user/', views.user_view, name='user'),
    path('logout/', views.logout_view, name='logout'),
    path('arrendador/<int:id>/', views.arrendador_profile_view, name='arrendador_profile'),
    path('alojamiento/<int:alojamiento_id>/', views.alojamiento_detalle_view, name='alojamiento_detalle'),
    path('user/<int:id>/', views.user_profile_view, name='user_profile'),
    path('admin_users/', views.admin_users_view, name='admin_users'),
    path('admin_users/actualizar/', views.actualizar_usuario, name='actualizar_usuario'),
    path('admin_users/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('admin_habitaciones/', views.admin_habitaciones_view, name='admin_habitaciones'),
    path('admin_control/', views.admin_control, name='admin_control'),
    path('admin_permisos/', views.admin_permisos, name='admin_permisos'),
    path('captcha/', generate_captcha, name='captcha'),
    path('actualizar_alojamiento/', actualizar_alojamiento, name='actualizar_alojamiento'),
    path('eliminar_alojamiento/', eliminar_alojamiento, name='eliminar_alojamiento'),
    path('alojamiento/editar/<int:alojamiento_id>/', editar_alojamiento_view, name='editar_alojamiento'),
    path('permissions/<int:admin_id>/update/', update_permission, name='update_permission'),
    path('verification_code/', verification_code_view, name='verification_code'),
    path('arrendador_verification_message/', views.arrendador_verification_message_view, name='arrendador_verification_message'),
    path('validar_rechazar_usuario/', validar_rechazar_usuario, name='validar_rechazar_usuario'),


 # Token de validación
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoints para Flutter
    path('api/usuarios/actualizar/', actualizar_perfil, name='actualizar_perfil'),
    path('api/login/', views.login_usuario, name='api-login'),
    path('api/usuarios/', views.UsuarioListCreate.as_view(), name='usuario-list-create'),
    path('api/usuarios/email/<str:email>/', views.UsuarioDetailByEmail.as_view(), name='usuario-detail-email'),
    path('api/alojamientos/', views.AlojamientoListCreate.as_view(), name='alojamiento-list-create'),
    path('api/alojamientos/<int:pk>/', views.AlojamientoDetail.as_view(), name='alojamiento-detail'),
    path('api/imagenes/', views.ImagenAlojamientoListCreate.as_view(), name='imagen-list-create'),
]
