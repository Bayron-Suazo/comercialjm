from django.urls import path
from empleado import views

urlpatterns = [
    #PERFIL
    path('perfil_empleado/', views.perfil_view, name='perfil_empleado'),

    # CLIENTES
    path('clientes/crear/', views.crear_cliente, name='crear_cliente_empleado'),
    path('clientes/activos/', views.listar_clientes_activos, name='listar_clientes_activos_empleado'),
    path('clientes/inactivos/', views.listar_clientes_inactivos, name='listar_clientes_inactivos_empleado'),
    path('clientes/ranking/', views.ranking_clientes, name='ranking_clientes_empleado'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente, name='editar_clientes_empleado'),
    path('clientes/<int:cliente_id>/compras/', views.detalle_compras_cliente, name='detalle_compras_cliente_empleado'),
    path('clientes/bloquear/', views.bloquear_cliente, name='bloquear_cliente_empleado'),
    path('clientes/activar/', views.activar_cliente, name='activar_cliente_empleado'),

    #VENTAS
    path('ventas/', views.listar_ventas, name='listar_ventas_empleado'),
    path('ventas/registrar/', views.registrar_venta, name='registrar_venta_empleado'),
    path('ventas/deshacer/<int:venta_id>/', views.deshacer_venta, name='deshacer_venta_empleado'),
    path('ventas/ver/<int:venta_id>/', views.ver_venta, name='ver_venta_empleado'),
    path('venta/<int:venta_id>/boleta/', views.generar_boleta_pdf, name='generar_boleta_empleado'),
    path('ventas/<int:venta_id>/factura/', views.generar_factura_pdf, name='generar_factura_pdf_empleado'),

    # COMPRAS
    path('lista_compras_activas/', views.lista_compras_activas, name='lista_compras_activas_empleado'),
    path('lista_compras_bloqueadas/', views.lista_compras_bloqueadas, name='lista_compras_bloqueadas_empleado'),
    path('registrar_compra/', views.registrar_compra_view, name='registrar_compra_empleado'),
    path('aprobar-compra/', views.aprobar_compra, name='aprobar_compra_empleado'),
    path('bloquear-compra/', views.bloquear_compra, name='bloquear_compra_empleado'),
    path('compra/<int:compra_id>/', views.detalle_compra, name='detalle_compra_empleado'),
]