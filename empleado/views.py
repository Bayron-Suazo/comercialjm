from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import PerfilForm
from django.views.decorators.http import require_POST
from empleado.forms import CompraForm, DetalleCompraForm 
from empleado.forms import AprobarCompraForm
from empleado.forms import VentaForm, DetalleVentaFormSet, DetalleVentaForm
from django.db.models import Count, Avg, Max, Min
from django.db import transaction
from collections import defaultdict
from django.forms import formset_factory
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Count, Sum, F, Q,  ExpressionWrapper, FloatField
from django.contrib import messages
from registration.models import Profile, Venta
from .forms import ClienteForm
from django.core.exceptions import ObjectDoesNotExist
from openpyxl import load_workbook
import traceback
from django.utils.crypto import get_random_string
from openpyxl.utils.datetime import from_excel
from django.utils.timezone import now, timedelta
import re, random, string, uuid, csv, json
from django.utils.dateparse import parse_date
from django.core.validators import validate_email
from django.template.loader import get_template
from weasyprint import HTML
from io import BytesIO
from django.forms import modelformset_factory
from decimal import Decimal
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from registration.models import Profile, Proveedor, Compra, Producto, DetalleCompra, DetalleLote, Lote, Cliente, ProductoUnidad, Merma, DetalleVenta
from datetime import datetime, date
from django.core.exceptions import ValidationError
from django.contrib import messages



# ------------------ PERFIL USUARIO ------------------



@login_required
def perfil_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        # Obtener datos del formulario
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()

        # Validar que no haya campos vacíos
        if not all([first_name, last_name, email, telefono, direccion]):
            return render(request, 'empleado/perfil.html', {'user': user})

        # Si pasa validación, actualizar datos
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        profile.telefono = telefono
        profile.direccion = direccion
        profile.save()

        return redirect('perfil_empleado')

    return render(request, 'empleado/perfil.html', {'user': user})



# ------------------------------------  GESTIÓN DE COMPRAS ------------------------------------



# ------------------ LISTADO DE COMPRAS ACTIVAS Y BLOQUEADAS ------------------



@login_required
def lista_compras_activas(request):
    order_by = request.GET.get('order_by', '')

    compras_activas = Compra.objects.filter(activo=True)

    if order_by:
        if order_by == 'proveedor':
            compras = compras_activas.order_by('proveedor')
        elif order_by == 'usuario':
            compras = compras_activas.order_by('usuario')
    else:
        compras = compras_activas.order_by('-id')
    
    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')
    compras = paginator.get_page(page_number)

    return render(request, 'empleado/lista_compras.html', {'compras': compras, 'order_by': order_by})



@login_required
def lista_compras_bloqueadas(request):
    order_by = request.GET.get('order_by', '')

    compras_bloqueadas = Compra.objects.filter(activo=False)

    if order_by:
        if order_by == 'proveedor':
            compras = compras_bloqueadas.order_by('proveedor')
        elif order_by == 'usuario':
            compras = compras_bloqueadas.order_by('usuario')
        else:
            compras = compras_bloqueadas.order_by('')
    else:
        compras = compras_bloqueadas.order_by('-id') 

    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')
    compras = paginator.get_page(page_number)

    return render(request, 'empleado/lista_compras_bloqueadas.html', {'compras': compras, 'order_by': order_by})



# ------------------ REGISTRAR - MOSTRAR - APROBAR - CANCELAR ------------------



@login_required
def registrar_compra_view(request):
    DetalleFormSet = formset_factory(DetalleCompraForm, extra=1, can_delete=True)
    
    try:
        proveedor_id = int(request.POST.get('proveedor') or request.GET.get('proveedor'))
        proveedor = Proveedor.objects.filter(id=proveedor_id).first()
    except (TypeError, ValueError):
        proveedor_id = None
        proveedor = None

    if request.method == 'POST' and 'submit' in request.POST:
        compra_form = CompraForm(request.POST)
        detalle_formset = DetalleFormSet(request.POST)
        
        if not proveedor:
            compra_form.add_error('proveedor', 'No se puede registrar una compra. Primero cargue los datos del proveedor y seleccione los productos que desea.')
            return render(request, 'empleado/registrar_compra.html', {
                'compra_form': compra_form,
                'detalle_formset': detalle_formset,
                'proveedor_seleccionado': proveedor,
            })

        # Actualizar queryset para producto_unidad filtrando por productos del proveedor activos
        for form in detalle_formset:
            form.fields['producto_unidad'].queryset = ProductoUnidad.objects.filter(
                producto__proveedores=proveedor,
                producto__activo=True
            )

        if compra_form.is_valid() and detalle_formset.is_valid():
            unidades_vistas = set()
            error_repetido = False

            formularios_validos = []

            for form in detalle_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    producto_unidad = form.cleaned_data['producto_unidad']

                    if producto_unidad in unidades_vistas:
                        form.add_error('producto_unidad', 'Esta unidad de producto ya fue ingresada.')
                        error_repetido = True
                    else:
                        unidades_vistas.add(producto_unidad)
                        formularios_validos.append(form)
            
            if not formularios_validos:
                detalle_formset.non_form_errors = lambda: ['Debe agregar al menos una unidad de producto para registrar la compra.']
                return render(request, 'empleado/registrar_compra.html', {
                    'compra_form': compra_form,
                    'detalle_formset': detalle_formset,
                    'proveedor_seleccionado': proveedor,
                })

            unidades_disponibles = ProductoUnidad.objects.filter(
                producto__proveedores=proveedor,
                producto__activo=True
            ).count()

            if len(formularios_validos) > unidades_disponibles:
                for form in detalle_formset:
                    form.add_error(None, "Se han ingresado más unidades de producto de las disponibles para este proveedor.")
                return render(request, 'empleado/registrar_compra.html', {
                    'compra_form': compra_form,
                    'detalle_formset': detalle_formset,
                    'proveedor_seleccionado': proveedor,
                })

            if error_repetido:
                return render(request, 'empleado/registrar_compra.html', {
                    'compra_form': compra_form,
                    'detalle_formset': detalle_formset,
                    'proveedor_seleccionado': proveedor,
                })

            compra = Compra.objects.create(
                proveedor=compra_form.cleaned_data['proveedor'],
                usuario=request.user,
                estado='Pendiente'
            )

            productos_solicitados = []

            for form in formularios_validos:
                producto_unidad = form.cleaned_data['producto_unidad']
                cantidad = form.cleaned_data['cantidad']
                observaciones = form.cleaned_data.get('observaciones', '')

                DetalleCompra.objects.create(
                    compra=compra,
                    producto_unidad=producto_unidad,
                    cantidad=cantidad,
                    observaciones=observaciones
                )

                texto = f"- {producto_unidad.producto.nombre} ({producto_unidad.get_unidad_medida_display()}): {cantidad} unidades"
                if observaciones:
                    texto += f" Nota: {observaciones}"

                productos_solicitados.append(texto)

            mensaje = f"""
Estimado/a {proveedor.nombre},

Le informamos que se ha registrado una nueva solicitud de compra con los siguientes productos:

{chr(10).join(productos_solicitados)}

Atentamente,
ComercialJM
            """

            send_mail(
                subject="Nueva solicitud de compra",
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[proveedor.correo],
                fail_silently=False,
            )

            return redirect('lista_compras_activas_empleado')

    else:
        compra_form = CompraForm(initial={'proveedor': proveedor_id})
        detalle_formset = DetalleFormSet()

        for form in detalle_formset:
            form.fields['producto_unidad'].queryset = ProductoUnidad.objects.filter(
                producto__proveedores=proveedor,
                producto__activo=True
            ) if proveedor else ProductoUnidad.objects.none()

    return render(request, 'empleado/registrar_compra.html', {
        'compra_form': compra_form,
        'detalle_formset': detalle_formset,
        'proveedor_seleccionado': proveedor,
    })




@csrf_exempt
def aprobar_compra(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido.'})

    compra_id = request.POST.get('compra_id')
    compra = get_object_or_404(Compra, id=compra_id)

    if compra.estado != 'Pendiente':
        return JsonResponse({'success': False, 'message': 'La compra ya fue procesada.'})

    form = AprobarCompraForm(request.POST, instance=compra)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'message': 'Formulario inválido: asegúrate de ingresar un total válido.'
        })

    # Guardamos el total
    form.save()

    # Cambiamos estado
    compra.estado = 'Lista'
    compra.activo = False
    compra.save()

    # Creamos Lote (solo con auto_now_add)
    lote = Lote.objects.create()

    # Para cada detalle de compra, creamos detalle de lote
    for detalle in compra.detalles.all():
        producto_unidad = detalle.producto_unidad
        cantidad = detalle.cantidad

        DetalleLote.objects.create(
            lote=lote,
            producto_unidad=producto_unidad,
            cantidad=cantidad
        )
        # No hacemos producto_unidad.cantidad += … ni producto_unidad.lote = …

    return JsonResponse({
        'success': True,
        'message': 'Compra aprobada, lote creado y stock actualizado correctamente.'
    })


@require_POST
def bloquear_compra(request):
    compra_id = request.POST.get('compra_id')

    try:
        compra = Compra.objects.get(id=compra_id)
        compra.estado = 'Cancelada'
        compra.activo = False
        compra.save()
        return JsonResponse({'success': True})
    except Compra.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Compra no encontrada'})
    

def detalle_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    return render(request, 'empleado/detalle_compra.html', {'compra': compra})




# -------------------------------------- MODULO CLIENTES --------------------------------------

@login_required
def listar_clientes_activos(request):
    order_by = request.GET.get('order_by', '')

    clientes_activos = Cliente.objects.filter(activo=True)

    if order_by:
        if order_by == 'nombre':
            clientes = clientes_activos.order_by('nombre')
        elif order_by == 'rut':
            clientes = clientes_activos.order_by('rut')
        else:
            clientes = clientes_activos
    else:
        clientes = clientes_activos

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    return render(request, 'empleado/listar_clientes_activos.html', {
        'clientes': clientes,
        'order_by': order_by
    })

@require_POST
@login_required
def bloquear_cliente(request):
    try:
        cliente_id = request.POST.get('cliente_id')
        cliente_ids = json.loads(request.POST.get('cliente_ids', '[]')) if request.POST.get('cliente_ids') else []

        if cliente_id:
            cliente_ids = [cliente_id]

        cliente_ids = [int(uid) for uid in cliente_ids]
        clientes = Cliente.objects.filter(id__in=cliente_ids, activo=True)
        updated_count = clientes.update(activo=False)

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def listar_clientes_inactivos(request):
    order_by = request.GET.get('order_by', '')

    clientes_bloqueados = Cliente.objects.filter(activo=False)

    if order_by:
        if order_by == 'nombre':
            clientes = clientes_bloqueados.order_by('nombre')
        elif order_by == 'rut':
            clientes = clientes_bloqueados.order_by('rut')
        else:
            clientes = clientes_bloqueados 
    else:
        clientes = clientes_bloqueados  

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    return render(
        request,
        'empleado/listar_clientes_inactivos.html',
        {'clientes': clientes, 'order_by': order_by}
    )


@require_POST
@login_required
def activar_cliente(request):
    try:
        cliente_id = request.POST.get('cliente_id')
        cliente_ids = json.loads(request.POST.get('cliente_ids', '[]')) if request.POST.get('cliente_ids') else []

        if cliente_id:
            cliente_ids = [int(cliente_id)]

        cliente_ids = [int(uid) for uid in cliente_ids]
        clientes = Cliente.objects.filter(id__in=cliente_ids, activo=False)

        updated_count = 0
        for cliente in clientes:
            cliente.activo = True
            cliente.save()
            updated_count += 1

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.activo = True
            cliente.save()
            return redirect('listar_clientes_activos_empleado')
        else:
            print("Errores del formulario:", form.errors) 
    else:
        form = ClienteForm()

    return render(request, 'empleado/crear_cliente.html', {'form': form})
    

def ranking_clientes(request):
    q = request.GET.get('q', '')

    clientes = Cliente.objects.filter(activo=True)

    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(rut__icontains=q) |
            Q(categoria__icontains=q)
        )

    clientes = clientes.annotate(
        total_ventas=Sum('ventas__total'),
        cantidad_ventas=Count('ventas')
    ).order_by('-cantidad_ventas')

    return render(request, 'empleado/ranking_clientes.html', {
        'clientes': clientes
    })


def dashboard_clientes(request):
    total_clientes = Cliente.objects.count()
    activos = Cliente.objects.filter(activo=True).count()
    inactivos = total_clientes - activos
    percent_activos = round((activos / total_clientes) * 100, 2) if total_clientes else 0
    percent_inactivos = round((inactivos / total_clientes) * 100, 2) if total_clientes else 0

    categorias = list(Cliente.objects.values_list('categoria', flat=True).distinct())
    cantidades = [Cliente.objects.filter(categoria=cat).count() for cat in categorias]

    ultimo_cliente = Cliente.objects.order_by('-id').first()

    context = {
        'total_clientes': total_clientes,
        'percent_activos': percent_activos,
        'percent_inactivos': percent_inactivos,
        'categorias': categorias,
        'cantidades': cantidades,
        'ultimo_cliente': ultimo_cliente
    }
    return render(request, 'empleado/dashboard_clientes.html', context)


def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes_activos_empleado')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'empleado/editar_clientes.html', {'form': form})


from django.db.models import Prefetch
def detalle_compras_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    ventas = Venta.objects.filter(cliente=cliente).prefetch_related(
        Prefetch('detalles', queryset=DetalleVenta.objects.select_related('producto_unidad__producto'))
    )

    return render(request, 'empleado/detalle_compras_cliente.html', {
        'cliente': cliente,
        'ventas': ventas
    })


# -------------------------------------- MODULO VENTAS --------------------------------------

@login_required
def listar_ventas(request):
    order_by = request.GET.get('order_by', '-id')
    ventas_activos = Venta.objects.all()

    if order_by:
        if order_by == 'id':
            ventas = ventas_activos.order_by('id')
        elif order_by == 'cliente':
            ventas = ventas_activos.order_by('cliente')
        elif order_by == 'usuario':
            ventas = ventas_activos.order_by('usuario')
        else:
            ventas = ventas_activos.order_by('-id')
    else:
        ventas = ventas_activos.order_by('-id')

    paginator = Paginator(ventas, 10)
    page_number = request.GET.get('page')
    ventas = paginator.get_page(page_number)

    return render(request, 'empleado/listar_ventas.html', {
        'ventas': ventas,
        'order_by': order_by
    })


@login_required
def registrar_venta(request):
    unidades = ProductoUnidad.objects.all()
    stock_map = {}
    price_map = {}
    clientes_info = {
        c.id: {
            'categoria': c.categoria.lower(),
            'contador_cupon': c.contador_cupon
        }
        for c in Cliente.objects.all()
    }
    for pu in unidades:
        total_stock = DetalleLote.objects.filter(
            producto_unidad=pu, cantidad__gt=0, lote__activo=True
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        stock_map[pu.id] = total_stock
        price_map[pu.id] = float(pu.precio)

    if request.method == 'POST':
        venta_form = VentaForm(request.POST)
        if venta_form.is_valid():
            venta = venta_form.save(commit=False)
            venta.usuario = request.user
            formset = DetalleVentaFormSet(request.POST, instance=venta)

            if formset.is_valid():
                detalles = formset.save(commit=False)
                detalles_validos = [
                    d for d in detalles
                    if d.cantidad > 0 and not getattr(d, 'DELETE', False)
                ]
                if not detalles_validos:
                    messages.error(request, "Debe agregar al menos un producto válido a la venta.")
                    return render(request, 'empleado/registrar_venta.html', {
                        'venta_form': venta_form,
                        'formset': formset,
                        'stock_map_json': json.dumps(stock_map),
                        'price_map_json': json.dumps(price_map),
                        'clientes_info_json': json.dumps(clientes_info),
                    })

                for detalle in detalles:
                    prod = detalle.producto_unidad
                    stock_total = (
                        DetalleLote.objects
                        .filter(producto_unidad=prod, cantidad__gt=0, lote__activo=True)
                        .aggregate(total=Sum('cantidad'))['total']
                        or 0
                    )
                    if detalle.cantidad > stock_total:
                        messages.error(
                            request,
                            f"No hay suficiente stock para {prod}. "
                            f"Disponible: {stock_total}, solicitado: {detalle.cantidad}"
                        )
                        return render(request, 'empleado/registrar_venta.html', {
                            'venta_form': venta_form,
                            'formset': formset,
                            'stock_map_json': json.dumps(stock_map),
                            'price_map_json': json.dumps(price_map),
                            'clientes_info_json': json.dumps(clientes_info),
                        })

                with transaction.atomic():
                    cliente = venta.cliente
                    descuento = 0

                    # Verificar y aplicar descuento si corresponde
                    if cliente:
                        cliente.contador_cupon += 1  # Incrementar contador

                        if cliente.categoria.lower() == "frecuente" and cliente.contador_cupon >= 50:
                            descuento = 10
                            cliente.contador_cupon = 0  # Reiniciar
                        elif cliente.categoria.lower() == "mayorista" and cliente.contador_cupon >= 30:
                            descuento = 15
                            cliente.contador_cupon = 0  # Reiniciar

                    venta.save()
                    total = 0

                    for detalle in detalles:
                        cantidad_rest = detalle.cantidad
                        for det_lote in (
                            DetalleLote.objects
                            .filter(producto_unidad=detalle.producto_unidad,
                                    cantidad__gt=0, lote__activo=True)
                            .order_by('lote__fecha')
                        ):
                            if cantidad_rest == 0:
                                break
                            if det_lote.cantidad >= cantidad_rest:
                                det_lote.cantidad -= cantidad_rest
                                det_lote.save()
                                cantidad_rest = 0
                            else:
                                cantidad_rest -= det_lote.cantidad
                                det_lote.cantidad = 0
                                det_lote.save()

                        detalle.venta = venta
                        detalle.save()
                        total += detalle.subtotal()

                    # Aplicar descuento si corresponde
                    if descuento:
                        total -= total * (Decimal(descuento) / Decimal('100'))

                    venta.total = total
                    venta.save()

                    if cliente:
                        cliente.save()  # Guardar cambios del contador

                return redirect('listar_ventas_empleado')

            else:
                return render(request, 'empleado/registrar_venta.html', {
                    'venta_form': venta_form,
                    'formset': formset,
                    'stock_map_json': json.dumps(stock_map),
                    'price_map_json': json.dumps(price_map),
                    'clientes_info_json': json.dumps(clientes_info),
                })
        else:
            formset = DetalleVentaFormSet(instance=Venta())
            return render(request, 'empleado/registrar_venta.html', {
                'venta_form': venta_form,
                'formset': formset,
                'stock_map_json': json.dumps(stock_map),
                'price_map_json': json.dumps(price_map),
                'clientes_info_json': json.dumps(clientes_info),
            })

    else:
        venta_form = VentaForm()
        formset = DetalleVentaFormSet(instance=Venta())
        return render(request, 'empleado/registrar_venta.html', {
            'venta_form': venta_form,
            'formset': formset,
            'stock_map_json': json.dumps(stock_map),
            'price_map_json': json.dumps(price_map),
            'clientes_info_json': json.dumps(clientes_info),
        })

from urllib.parse import unquote

def generar_boleta_pdf(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    detalles = venta.detalles.select_related('producto_unidad', 'producto_unidad__producto')

    nombre_cliente = request.GET.get('nombre_cliente')
    rut_cliente = request.GET.get('rut_cliente')
    direccion_cliente = request.GET.get('direccion_cliente')

    if nombre_cliente: nombre_cliente = unquote(nombre_cliente)
    if rut_cliente: rut_cliente = unquote(rut_cliente)
    if direccion_cliente: direccion_cliente = unquote(direccion_cliente)

    # Calcular subtotal
    subtotal = detalles.aggregate(
        subtotal=Sum(
            ExpressionWrapper(
                F('cantidad') * F('producto_unidad__precio'),
                output_field=DecimalField()
            )
        )
    )['subtotal'] or Decimal('0')

    subtotal = subtotal.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    total = venta.total.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    if subtotal > 0:
        descuento_porcentaje = ((subtotal - total) * 100 / subtotal).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    else:
        descuento_porcentaje = Decimal('0')

    monto_descuento = (subtotal - total).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    html_string = render_to_string('empleado/boleta_pdf.html', {
        'venta': venta,
        'detalles': detalles,
        'nombre_cliente_manual': nombre_cliente,
        'rut_cliente_manual': rut_cliente,
        'direccion_cliente_manual': direccion_cliente,
        'subtotal': subtotal,
        'monto_descuento': monto_descuento,
        'descuento_porcentaje': descuento_porcentaje,
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=boleta_venta_{venta.id}.pdf'
    html.write_pdf(response)
    return response

def generar_factura_pdf(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    detalles = venta.detalles.select_related('producto_unidad', 'producto_unidad__producto')

    subtotal = sum([d.subtotal() for d in detalles])
    subtotal = Decimal(subtotal).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    total_venta = venta.total.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    descuento = (subtotal - total_venta).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    if subtotal > 0:
        descuento_porcentaje = ((descuento * 100) / subtotal).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    else:
        descuento_porcentaje = Decimal('0')

    # Calcular IVA y total con IVA en base al total de venta
    iva = (total_venta * Decimal('0.19')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    total_con_iva = total_venta + iva

    if venta.cliente is None:
        nombre_cliente = request.GET.get('nombre_cliente', 'Cliente no registrado')
        rut_cliente = request.GET.get('rut_cliente', 'Sin RUT')
        direccion_cliente = request.GET.get('direccion_cliente', 'Sin dirección')
        giro_cliente = request.GET.get('giro_cliente', 'Particular')
    else:
        nombre_cliente = venta.cliente.nombre
        rut_cliente = venta.cliente.rut
        direccion_cliente = venta.cliente.direccion
        giro_cliente = request.GET.get('giro_cliente') or venta.cliente.giro or 'No informado'

    html_string = render_to_string('empleado/factura_pdf.html', {
        'venta': venta,
        'detalles': detalles,
        'subtotal': subtotal,
        'descuento': descuento,
        'descuento_porcentaje': descuento_porcentaje,
        'iva': iva,
        'total': total_con_iva,
        'nombre_cliente': nombre_cliente,
        'rut_cliente': rut_cliente,
        'direccion_cliente': direccion_cliente,
        'giro_cliente': giro_cliente,
        'emisor': settings.EMPRESA_EMISOR,
        'rut_emisor': settings.EMPRESA_RUT,
        'direccion_emisor': settings.EMPRESA_DIRECCION,
        'giro_emisor': settings.EMPRESA_GIRO,
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=factura_venta_{venta.id}.pdf'
    html.write_pdf(response)
    return response


@login_required
def deshacer_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles_venta = DetalleVenta.objects.filter(venta=venta)
    errores = []

    for detalle in detalles_venta:
        producto_unidad = detalle.producto_unidad
        cantidad_a_restaurar = detalle.cantidad

        lotes_disponibles = DetalleLote.objects.filter(
            producto_unidad=producto_unidad,
            cantidad__gte=0
        ).order_by('lote__fecha')

        if not lotes_disponibles.exists():
            errores.append(f"No hay lotes disponibles para restaurar el stock de {producto_unidad}.")
            continue

        for detalle_lote in lotes_disponibles:
            if cantidad_a_restaurar <= 0:
                break
            detalle_lote.cantidad += cantidad_a_restaurar
            detalle_lote.save()
            cantidad_a_restaurar = 0

        if cantidad_a_restaurar > 0:
            errores.append(f"No se pudo restaurar completamente el stock de {producto_unidad}.")

    if errores:
        messages.error(request, "Algunas cantidades no pudieron ser restauradas:\n" + "\n".join(errores))
        return redirect('listar_ventas_empleado')

    venta.delete()
    messages.success(request, "La venta fue deshecha correctamente y el stock fue restaurado.")
    return redirect('listar_ventas_empleado')


@login_required
def ver_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = venta.detalles.select_related('producto_unidad__producto')

    subtotal = detalles.aggregate(
        subtotal=Sum(
            ExpressionWrapper(
                F('cantidad') * F('producto_unidad__precio'),
                output_field=DecimalField()
            )
        )
    )['subtotal'] or Decimal('0')

    subtotal = subtotal.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    total = venta.total.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    if subtotal > 0:
        descuento_porcentaje = ((subtotal - total) * 100 / subtotal).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    else:
        descuento_porcentaje = Decimal('0')

    monto_descuento = (subtotal - total).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    context = {
        'venta': venta,
        'detalles': detalles,
        'subtotal': subtotal,
        'monto_descuento': monto_descuento,
        'descuento_porcentaje': descuento_porcentaje,
    }
    return render(request, 'empleado/detalle_venta.html', context)