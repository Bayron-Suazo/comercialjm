from django.urls import path
from . import views

urlpatterns = [
    path('perfil/', views.perfil_view, name='perfil'),
]