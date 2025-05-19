from django.urls import path 
from core import views 

core_urlpatterns = [
    path('', views.home, name='home'),    
    path('check_profile', views.check_profile, name='check_profile'),
    path('seleccionar_rol',views.seleccionar_rol, name='seleccionar_rol'),           
    ]
from django.urls import path
from . import views

urlpatterns = [
    path('bloquear-lote/<int:id>/', views.bloquear_lote, name='bloquear_lote'),
    path('lotes/', views.listar_lotes, name='listar_lotes'),
    path('productos/inactivos/', views.productos_inactivos, name='productos_inactivos'),
    path('productos/', views.listar_productos, name='listar_productos'),
    path('productos/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/toggle/<int:id>/', views.toggle_estado_producto, name='toggle_estado_producto'),
    path('productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),

    path('debug/', views.debug_url_test),

]
