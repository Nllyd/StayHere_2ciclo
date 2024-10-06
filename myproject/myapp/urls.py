from django.urls import path
from . import views

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
    path('alojamiento/<int:alojamiento_id>/', views.alojamiento_detalle_view, name='alojamiento_detalle'),
    path('user/<int:id>/', views.user_profile_view, name='user_profile'),
    path('admin_users/', views.admin_users_view, name='admin_users'),
    path('admin_users/actualizar/', views.actualizar_usuario, name='actualizar_usuario'),
    path('admin_users/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('admin_habitaciones/', views.admin_habitaciones_view, name='admin_habitaciones'),
    path('admin_control/', views.admin_control, name='admin_control'),
    path('admin_permisos/', views.admin_permisos, name='admin_permisos')
]
