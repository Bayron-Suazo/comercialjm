from django.urls import path
from . import views

urlpatterns = [
    path('prueba/', views.pagina_prueba, name='pagina_prueba'),
]