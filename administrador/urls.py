from django.urls import path
from . import views

urlpatterns = [
    
    # USUARIOS
    path('lista_usuarios_activos/', views.lista_usuarios_activos, name='lista_usuarios_activos'),
    path('lista_usuarios_bloqueados/', views.lista_usuarios_bloqueados, name='lista_usuarios_bloqueados'),
    path('agregar_usuario/', views.agregar_usuario, name='agregar_usuario'),
    path('bloquear-usuario/', views.bloquear_usuario, name='bloquear_usuario'),
    path('activar-usuario/', views.activar_usuario, name='activar_usuario'),
    path('mostrar_usuario/<int:user_id>/', views.mostrar_usuario, name='mostrar_usuario'),
    path('editar_usuario/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('perfil_admin/', views.perfil_view, name='perfil_admin'),
    path('dashboard_usuarios/', views.dashboard_usuarios, name='dashboard_usuarios'),
    path('usuarios/carga-masiva/', views.carga_masiva_usuarios, name='carga_masiva_usuarios'),
    path('usuarios/<int:user_id>/cambiar-credenciales/', views.cambiar_credenciales, name='cambiar_credenciales'),


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
    path('proveedores/carga-masiva/', views.carga_masiva_proveedores, name='carga_masiva_proveedores'),


    # COMPRAS
    path('lista_compras_activas/', views.lista_compras_activas, name='lista_compras_activas'),
    path('lista_compras_bloqueadas/', views.lista_compras_bloqueadas, name='lista_compras_bloqueadas'),
    path('registrar_compra/', views.registrar_compra_view, name='registrar_compra'),
    path('aprobar-compra/', views.aprobar_compra, name='aprobar_compra'),
    path('bloquear-compra/', views.bloquear_compra, name='bloquear_compra'),
    path('compra/<int:compra_id>/', views.detalle_compra, name='detalle_compra'),
    path('dashboard_compras/', views.dashboard_compras, name='dashboard_compras'),


    # CLIENTES
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/dashboard/', views.dashboard_clientes, name='dashboard_clientes'),
    path('clientes/activos/', views.listar_clientes_activos, name='listar_clientes_activos'),
    path('clientes/inactivos/', views.listar_clientes_inactivos, name='listar_clientes_inactivos'),
    path('clientes/ranking/', views.ranking_clientes, name='ranking_clientes'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente, name='editar_clientes'),
    path('clientes/<int:cliente_id>/compras/', views.detalle_compras_cliente, name='detalle_compras_cliente'),
    path('clientes/bloquear/', views.bloquear_cliente, name='bloquear_cliente'),
    path('clientes/activar/', views.activar_cliente, name='activar_cliente'),


    # PRODUCTOS
    path('mermas/registrar/', views.registrar_merma, name='registrar_merma'),
    path('mermas/<int:merma_id>/', views.detalle_merma, name='detalle_merma'),
    path('mermas/<int:merma_id>/deshacer/', views.deshacer_merma, name='deshacer_merma'),
    path('mermas/', views.listar_mermas, name='listar_mermas'),
    path('productos/dashboard/', views.dashboard_productos, name='dashboard_productos'),
    path('productos/dashboard/', views.dashboard_productos, name='dashboard_productos'),
    path('productos/inactivos/', views.listar_productos_bloqueados, name='productos_inactivos'),
    path('productos/', views.listar_productos, name='listar_productos'),
    path('productos/agregar/', views.agregar_producto, name='agregar_producto'),
    path('productos/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('productos/bloquear/', views.bloquear_productos, name='bloquear_productos'),
    path('productos/activar/', views.activar_productos, name='activar_productos'),
    path('lotes/', views.listar_lotes, name='listar_lotes'),
    path('lotes/ver/<int:lote_id>/', views.ver_lote, name='ver_lote'),
    path('lotes/agregar/', views.agregar_lote, name='agregar_lote'),


    #VENTAS
    path('ventas/dashboard/', views.dashboard_ventas, name='dashboard_ventas'),
    path('ventas/', views.listar_ventas, name='listar_ventas'),
    path('ventas/registrar/', views.registrar_venta, name='registrar_venta'),
    path('ventas/deshacer/<int:venta_id>/', views.deshacer_venta, name='deshacer_venta'),
    path('ventas/ver/<int:venta_id>/', views.ver_venta, name='ver_venta'),
    path('venta/<int:venta_id>/boleta/', views.generar_boleta_pdf, name='generar_boleta'),
    path('ventas/<int:venta_id>/factura/', views.generar_factura_pdf, name='generar_factura_pdf'),


    #REPORTERIA
    path('reporteria/', views.reporteria_view, name='reporteria'),
    path('reporteria_pdf/', views.reporteria_pdf_view, name='reporteria_pdf'),

]