from django.urls import path
from . import views

urlpatterns = [
    path('prueba/', views.pagina_prueba, name='pagina_prueba'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/agregar/', views.agregar_usuario, name='agregar_usuario'),
]