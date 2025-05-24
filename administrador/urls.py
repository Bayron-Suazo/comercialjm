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
    path('perfil_admin/', views.perfil_view, name='perfil_admin'),
    path('dashboard_usuarios/', views.dashboard_usuarios, name='dashboard_usuarios'),

    path('lista_proveedores_activos/', views.lista_proveedores_activos, name='lista_proveedores_activos'),
    path('lista_proveedores_bloqueados/', views.lista_proveedores_bloqueados, name='lista_proveedores_bloqueados'),
    path('agregar_proveedor/', views.agregar_proveedor, name='agregar_proveedor'),
    path('bloquear_proveedor/', views.bloquear_proveedor, name='bloquear_proveedor'),
    path('activar_proveedor/', views.activar_proveedor, name='activar_proveedor'),
    path('mostrar_proveedor/<int:proveedor_id>/', views.mostrar_proveedor, name='mostrar_proveedor'),
    path('editar_proveedor/<int:proveedor_id>/', views.editar_proveedor, name='editar_proveedor'),
    path('dashboard_proveedores/', views.dashboard_proveedores, name='dashboard_proveedores'),
    path('proveedor/<int:proveedor_id>/asignar_productos/', views.asignar_productos, name='asignar_producto_proveedor'),

    path('lista_compras_activas/', views.lista_compras_activas, name='lista_compras_activas'),
    path('lista_compras_bloqueadas/', views.lista_compras_bloqueadas, name='lista_compras_bloqueadas'),
]