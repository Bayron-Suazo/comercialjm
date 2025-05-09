from django.urls import path
from . import views

urlpatterns = [
    path('lista_usuarios_activos/', views.lista_usuarios_activos, name='lista_usuarios_activos'),
    path('lista_usuarios_bloqueados/', views.lista_usuarios_bloqueados, name='lista_usuarios_bloqueados'),
    path('usuarios/agregar/', views.agregar_usuario, name='agregar_usuario'),
]