from django.urls import path
from . import views

urlpatterns = [
    
    # USUARIOS
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


    # PROVEEDORES
    path('lista_proveedores_activos/', views.lista_proveedores_activos, name='lista_proveedores_activos'),
    path('lista_proveedores_bloqueados/', views.lista_proveedores_bloqueados, name='lista_proveedores_bloqueados'),
    path('agregar_proveedor/', views.agregar_proveedor, name='agregar_proveedor'),
    path('bloquear_proveedor/', views.bloquear_proveedor, name='bloquear_proveedor'),
    path('activar_proveedor/', views.activar_proveedor, name='activar_proveedor'),
    path('mostrar_proveedor/<int:proveedor_id>/', views.mostrar_proveedor, name='mostrar_proveedor'),
    path('editar_proveedor/<int:proveedor_id>/', views.editar_proveedor, name='editar_proveedor'),
    path('dashboard_proveedores/', views.dashboard_proveedores, name='dashboard_proveedores'),
    path('proveedor/<int:proveedor_id>/asignar_productos/', views.asignar_productos, name='asignar_producto_proveedor'),


    # COMPRAS
    path('lista_compras_activas/', views.lista_compras_activas, name='lista_compras_activas'),
    path('lista_compras_bloqueadas/', views.lista_compras_bloqueadas, name='lista_compras_bloqueadas'),
    path('registrar_compra/', views.registrar_compra_view, name='registrar_compra'),


    # PRODUCTOS
    path('lotes/carga_excel/', views.carga_excel_lotes, name='carga_excel_lotes'),
    path('clientes/<int:pk>/desactivar/', views.toggle_estado_cliente, name='toggle_estado_cliente'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/eliminar/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('clientes/dashboard/', views.dashboard_clientes, name='dashboard_clientes'),
    path('clientes/activos/', views.listar_clientes_activos, name='listar_clientes_activos'),
    path('clientes/inactivos/', views.listar_clientes_inactivos, name='listar_clientes_inactivos'),
    path('clientes/ranking/', views.ranking_clientes, name='ranking_clientes'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente, name='editar_clientes'),
    path('mermas/agregar/', views.agregar_merma, name='agregar_merma'),
    path('productos/dashboard/', views.dashboard_productos, name='dashboard_productos'),
    path('mermas/', views.listar_mermas, name='listar_mermas'),
    path('productos/dashboard/', views.dashboard_productos, name='dashboard_productos'),
    path('productos/inactivos/', views.productos_inactivos, name='productos_inactivos'),
    path('productos/', views.listar_productos, name='listar_productos'),
    path('productos/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/<int:id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/<int:id>/lotes/', views.ver_lotes_producto, name='ver_lotes_producto'),
    path('productos/toggle/<int:id>/', views.toggle_estado_producto, name='toggle_estado_producto'),
    path('productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('lotes/', views.listar_lotes, name='listar_lotes'),
    path('lotes/carga_excel/', views.carga_excel_lotes, name='carga_excel_lotes'),
    path('lotes/eliminar/<int:lote_id>/', views.eliminar_lote, name='eliminar_lote'),
    path('lotes/ver/<int:id>/', views.ver_lote, name='ver_lote'),
    path('ventas/dashboard/', views.dashboard_ventas, name='dashboard_ventas'),
    path('ventas/', views.listar_ventas, name='listar_ventas'),
    path('debug/', views.debug_url_test),
]