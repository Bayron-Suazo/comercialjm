from django.urls import path
from . import views

urlpatterns = [
    path('lista_usuarios_activos/', views.lista_usuarios_activos, name='lista_usuarios_activos'),
    path('lista_usuarios_bloqueados/', views.lista_usuarios_bloqueados, name='lista_usuarios_bloqueados'),
    path('agregar_usuario/', views.agregar_usuario, name='agregar_usuario'),
    path('cargar-usuarios/', views.cargar_usuarios, name='cargar_usuarios'),
    path('bloquear-usuario/', views.bloquear_usuario, name='bloquear_usuario'),
    path('activar-usuario/', views.activar_usuario, name='activar_usuario'),
    path('mostrar_usuario/<int:user_id>/', views.mostrar_usuario, name='mostrar_usuario'),
    path('editar_usuario/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('perfil/', views.perfil_view, name='perfil'),
]