from django.urls import path
from . import views

urlpatterns = [
    path('prueba/', views.pagina_prueba_empleado, name='pagina_prueba_empleado'),
]