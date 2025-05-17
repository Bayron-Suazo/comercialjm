from django.urls import path
from empleado import views

urlpatterns = [
    path('perfil_empleado/', views.perfil_view, name='perfil_empleado'),
]