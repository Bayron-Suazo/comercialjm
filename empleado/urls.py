from django.urls import path
from empleado import views

urlpatterns = [
    #PERFIL
    path('perfil_empleado/', views.perfil_view, name='perfil_empleado'),

    # CLIENTES
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/activos/', views.listar_clientes_activos, name='listar_clientes_activos'),
    path('clientes/inactivos/', views.listar_clientes_inactivos, name='listar_clientes_inactivos'),
    path('clientes/ranking/', views.ranking_clientes, name='ranking_clientes'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente, name='editar_clientes'),
    path('clientes/<int:cliente_id>/compras/', views.detalle_compras_cliente, name='detalle_compras_cliente'),
    path('clientes/bloquear/', views.bloquear_cliente, name='bloquear_cliente'),
    path('clientes/activar/', views.activar_cliente, name='activar_cliente'),

    #VENTAS
    path('ventas/', views.listar_ventas, name='listar_ventas'),
    path('ventas/registrar/', views.registrar_venta, name='registrar_venta'),
    path('ventas/deshacer/<int:venta_id>/', views.deshacer_venta, name='deshacer_venta'),
    path('ventas/ver/<int:venta_id>/', views.ver_venta, name='ver_venta'),
    path('venta/<int:venta_id>/boleta/', views.generar_boleta_pdf, name='generar_boleta'),
    path('ventas/<int:venta_id>/factura/', views.generar_factura_pdf, name='generar_factura_pdf'),

    # COMPRAS
    path('lista_compras_activas/', views.lista_compras_activas, name='lista_compras_activas'),
    path('lista_compras_bloqueadas/', views.lista_compras_bloqueadas, name='lista_compras_bloqueadas'),
    path('registrar_compra/', views.registrar_compra_view, name='registrar_compra'),
    path('aprobar-compra/', views.aprobar_compra, name='aprobar_compra'),
    path('bloquear-compra/', views.bloquear_compra, name='bloquear_compra'),
    path('compra/<int:compra_id>/', views.detalle_compra, name='detalle_compra'),
]