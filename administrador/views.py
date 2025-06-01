import csv
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from .forms import UserProfileForm
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import CargaMasivaUsuariosForm
from registration.models import Profile, Proveedor, Compra, Producto, DetalleCompra, Merma, DetalleLote, Lote, Cliente
from datetime import datetime
from django.core.exceptions import ValidationError
from django.contrib import messages
from administrador.forms import EditUserProfileForm, CrearProveedorForm, EditarProveedorForm, CompraForm, DetalleCompraForm
from django.views.decorators.http import require_POST
from .forms import PerfilForm
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
from django.db.models import Count
from django.contrib import messages
from .forms import ProductoForm, MermaForm
from registration.models import Profile, Venta
from .forms import ClienteForm
from django.core.exceptions import ObjectDoesNotExist
import uuid

# ------------------------------------ GESTIÓN DE USUARIOS ------------------------------------



# ------------------ LISTADO DE USUARIOS ACTIVOS Y BLOQUEADOS ------------------



@login_required
def lista_usuarios_activos(request):
    order_by = request.GET.get('order_by', '')

    usuarios_activos = User.objects.filter(is_active=True)

    if order_by:
        if order_by == 'first_name':
            usuarios = usuarios_activos.order_by('first_name')
        elif order_by == 'last_name':
            usuarios = usuarios_activos.order_by('last_name')
        elif order_by == 'rut':
            usuarios = usuarios_activos.order_by('profile__rut')
        else:
            usuarios = usuarios_activos
    else:
        usuarios = usuarios_activos
    
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'administrador/lista_usuarios.html', {'usuarios': usuarios, 'order_by': order_by})



@login_required
def lista_usuarios_bloqueados(request):
    order_by = request.GET.get('order_by', '')

    usuarios_bloqueados = User.objects.filter(is_active=False)

    if order_by:
        if order_by == 'first_name':
            usuarios = usuarios_bloqueados.order_by('first_name')
        elif order_by == 'last_name':
            usuarios = usuarios_bloqueados.order_by('last_name')
        elif order_by == 'rut':
            usuarios = usuarios_bloqueados.order_by('profile__rut')
        elif order_by == 'group':
            usuarios = usuarios_bloqueados.order_by('groups__name')
        else:
            usuarios = usuarios_bloqueados 
    else:
        usuarios = usuarios_bloqueados  

    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'administrador/lista_usuarios_bloqueados.html', {'usuarios': usuarios, 'order_by': order_by})



# ------------------ AGREGAR - MOSTRAR - EDITAR - ACTIVAR - BLOQUEAR ------------------



@login_required
def agregar_usuario(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            profile, password = form.save()
            user = profile.user

            # Enviar correo
            asunto = f"Cuenta creada correctamente en Comercial JM para {user.first_name} {user.last_name}"
            mensaje = f"""
                Hola {user.first_name} {user.last_name},

                Tu cuenta en Comercial JM ha sido creada exitosamente.

                Puedes acceder al sistema en el siguiente enlace:
                http://127.0.0.1:8000/accounts/login/

                Tus credenciales de acceso son:

                Usuario: {user.username}
                Contraseña: {password}

                Por seguridad, te recomendamos cambiar tu contraseña después de iniciar sesión.

                Saludos cordiales,  
                Equipo Comercial JM
            """

            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return redirect('lista_usuarios_activos')
    else:
        form = UserProfileForm()
    return render(request, 'administrador/agregar_usuario.html', {'form': form})



@login_required
def mostrar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'administrador/mostrar_usuario.html', {'user': user})



@login_required
def editar_usuario(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile = get_object_or_404(Profile, user=user)

    if request.method == 'POST':
        form = EditUserProfileForm(request.POST, instance=profile, user_instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = EditUserProfileForm(instance=profile, user_instance=user)
        return render(request, 'administrador/editar_usuario.html', {
            'user_form': form,
            'user': user
        })



@user_passes_test(lambda u: u.is_superuser)
@require_POST
@login_required
def activar_usuario(request):
    try:
        user_id = request.POST.get('user_id')
        user_ids = json.loads(request.POST.get('user_ids', '[]')) if request.POST.get('user_ids') else []

        if user_id:
            if int(user_id) == request.user.id:
                return JsonResponse({'success': False})
            user_ids = [user_id]

        user_ids = [int(uid) for uid in user_ids if int(uid) != request.user.id]
        users = User.objects.filter(id__in=user_ids, is_active=False)

        from registration.models import Profile
        updated_count = 0

        for user in users:
            user.is_active = True
            user.save()
            Profile.objects.filter(user=user).update(failed_attempts=0)
            updated_count += 1

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@user_passes_test(lambda u: u.is_superuser)
@require_POST
@login_required
def bloquear_usuario(request):
    try:
        user_id = request.POST.get('user_id')
        user_ids = json.loads(request.POST.get('user_ids', '[]')) if request.POST.get('user_ids') else []

        if user_id:
            if int(user_id) == request.user.id:
                return JsonResponse({'success': False})
            user_ids = [user_id]

        user_ids = [int(uid) for uid in user_ids if int(uid) != request.user.id]
        users = User.objects.filter(id__in=user_ids, is_active=True)
        updated_count = users.update(is_active=False)

        return JsonResponse({'success': True, 'updated': updated_count})
    except:
        return JsonResponse({'success': False})
    


# ------------------ VISTA PERFIL ------------------



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
            return render(request, 'administrador/perfil.html', {'user': user})

        # Si pasa validación, actualizar datos
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        profile.telefono = telefono
        profile.direccion = direccion
        profile.save()

        return redirect('perfil_admin')

    return render(request, 'administrador/perfil.html', {'user': user})



# ------------------ CARGA MASIVA ------------------



def cargar_usuarios(request):
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo_csv = request.FILES["archivo"]
        try:
            decoded_file = archivo_csv.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            for row in reader:
                try:
                    required_fields = [
                        'rut', 'email', 'first_name', 'last_name',
                        'fecha_nacimiento', 'sexo', 'direccion', 'cargo', 'telefono'
                    ]
                    for field in required_fields:
                        if not row.get(field):
                            raise ValidationError(f"El campo '{field}' es obligatorio.")

                    if User.objects.filter(username=row['rut']).exists():
                        raise ValidationError(f"El usuario con RUT {row['rut']} ya existe.")

                    cargo = row['cargo'].strip().lower()
                    if cargo not in ['empleado', 'administrador']:
                        raise ValidationError(f"El cargo {row['cargo']} no es válido.")

                    grupo = Group.objects.get(name=cargo.capitalize())

                    user = User.objects.create_user(
                        username=row['rut'],
                        email=row['email'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        password='contraseña_default'
                    )
                    user.is_active = True
                    user.save()

                    profile = Profile.objects.create(
                        user=user,
                        rut=row['rut'],
                        fecha_nacimiento=convert_date(row['fecha_nacimiento']),
                        sexo=row['sexo'],
                        direccion=row['direccion'],
                        telefono=row['telefono']
                    )

                    # Asignar grupo al perfil y al usuario
                    profile.groups.add(grupo)
                    user.groups.add(grupo)
                    user.save()

                    print(f"[USUARIO CREADO] {user.username}")

                except ValidationError as e:
                    print(f"[VALIDATION ERROR] {e}")
                    messages.error(request, str(e))
                except Exception as e:
                    print(f"[ERROR] {row.get('rut', 'desconocido')}: {e}")
                    messages.error(request, f"Error al procesar usuario {row.get('rut', 'desconocido')}: {e}")

            messages.success(request, "Carga masiva completada.")
            return redirect("lista_usuarios_activos")

        except Exception as e:
            messages.error(request, f"Error al procesar archivo: {e}")
            return redirect("lista_usuarios_activos")

    return redirect("lista_usuarios_activos")



# Función para convertir las fechas al formato YYYY-MM-DD
def convert_date(date_str):
    try:
        # Convertir de 'DD/MM/YYYY' a 'YYYY-MM-DD'
        return datetime.strptime(date_str, '%d/%m/%Y').date()
    except ValueError:
        return None



# ------------------ DASHBOARD DE USUARIOS ------------------



@login_required
def dashboard_usuarios(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users

    percent_active = (active_users / total_users * 100) if total_users else 0
    percent_inactive = 100 - percent_active

    empleados_group = Group.objects.get(name="Empleado")
    administradores_group = Group.objects.get(name="Administrador")

    empleados = User.objects.filter(groups=empleados_group).count()
    administradores = User.objects.filter(groups=administradores_group).count()
    ambos = User.objects.annotate(num_groups=Count('groups')).filter(num_groups__gt=1).count()

    ultimo_usuario = User.objects.latest('date_joined')

    context = {
        'total_users': total_users,
        'percent_active': round(percent_active, 2),
        'percent_inactive': round(percent_inactive, 2),
        'empleados': empleados,
        'administradores': administradores,
        'ambos': ambos,
        'ultimo_usuario': ultimo_usuario,
    }

    return render(request, 'administrador/dashboard_usuarios.html', context)



# ------------------------------------ FIN GESTIÓN DE USUARIOS ------------------------------------



# ------------------------------------ GESTIÓN DE PROVEEDORES ------------------------------------



# ------------------ LISTADO DE PROVEEDORES ACTIVOS Y BLOQUEADOS ------------------



@login_required
def lista_proveedores_activos(request):
    order_by = request.GET.get('order_by', '')

    proveedores_activos = Proveedor.objects.filter(estado=True)

    if order_by:
        if order_by == 'nombre':
            proveedores = proveedores_activos.order_by('nombre')
        elif order_by == 'rut':
            proveedores = proveedores_activos.order_by('rut')
        else:
            proveedores = proveedores_activos
    else:
        proveedores = proveedores_activos
    
    paginator = Paginator(proveedores, 10)
    page_number = request.GET.get('page')
    proveedores = paginator.get_page(page_number)

    return render(request, 'administrador/lista_proveedores.html', {'proveedores': proveedores, 'order_by': order_by})



@login_required
def lista_proveedores_bloqueados(request):
    order_by = request.GET.get('order_by', '')

    proveedores_bloqueados = Proveedor.objects.filter(estado=False)

    if order_by:
        if order_by == 'nombre':
            proveedores = proveedores_bloqueados.order_by('nombre')
        elif order_by == 'rut':
            proveedores = proveedores_bloqueados.order_by('rut')
        else:
            proveedores = proveedores_bloqueados 
    else:
        proveedores = proveedores_bloqueados  

    paginator = Paginator(proveedores, 10)
    page_number = request.GET.get('page')
    proveedores = paginator.get_page(page_number)

    return render(request, 'administrador/lista_proveedores_bloqueados.html', {'proveedores': proveedores, 'order_by': order_by})



# ------------------ AGREGAR - MOSTRAR - EDITAR - ACTIVAR - BLOQUEAR ------------------



def agregar_proveedor(request):
    if request.method == 'POST':
        form = CrearProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            return redirect('mostrar_proveedor', proveedor_id=proveedor.id)
    else:
        form = CrearProveedorForm()
    
    return render(request, 'administrador/agregar_proveedor.html', {'form': form})



@user_passes_test(lambda u: u.is_superuser)
@require_POST
@login_required
def activar_proveedor(request):
    try:
        proveedor_id = request.POST.get('proveedor_id')
        proveedor_ids = json.loads(request.POST.get('proveedor_ids', '[]')) if request.POST.get('proveedor_ids') else []

        if proveedor_id:
            proveedor_ids = [int(proveedor_id)]

        proveedor_ids = [int(uid) for uid in proveedor_ids]
        proveedores = Proveedor.objects.filter(id__in=proveedor_ids, estado=False)

        updated_count = 0
        for proveedor in proveedores:
            proveedor.estado = True
            proveedor.save()
            updated_count += 1

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    


@user_passes_test(lambda u: u.is_superuser)
@require_POST
@login_required
def bloquear_proveedor(request):
    try:
        proveedor_id = request.POST.get('proveedor_id')
        proveedor_ids = json.loads(request.POST.get('proveedor_ids', '[]')) if request.POST.get('proveedor_ids') else []

        if proveedor_id:
            proveedor_ids = [proveedor_id]

        proveedor_ids = [int(uid) for uid in proveedor_ids]
        proveedores = Proveedor.objects.filter(id__in=proveedor_ids, estado=True)
        updated_count = proveedores.update(estado=False)

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    


@login_required
def mostrar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    return render(request, 'administrador/mostrar_proveedor.html', {'proveedor': proveedor})    



@login_required
def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)

    if request.method == 'POST':
        form = EditarProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = EditarProveedorForm(instance=proveedor)
        return render(request, 'administrador/editar_proveedor.html', {
            'proveedor_form': form,
            'proveedor': proveedor
        })



def asignar_productos(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    order_by = request.GET.get('order_by', 'nombre')

    productos = Producto.objects.filter(activo=True).order_by(order_by)

    if request.method == 'POST':
        ids_productos_seleccionados = request.POST.getlist('productos[]')
        ids_productos_seleccionados = list(map(int, ids_productos_seleccionados))

        proveedor.productos.set(ids_productos_seleccionados)

        return redirect('mostrar_proveedor', proveedor_id=proveedor.id)

    context = {
        'proveedor': proveedor,
        'productos': productos,
        'order_by': order_by,
        'productos_asignados_ids': proveedor.productos.values_list('id', flat=True),
    }
    return render(request, 'administrador/asignar_producto_proveedor.html', context)



# ------------------ DASHBOARD DE PROVEEDORES ------------------



@login_required
def dashboard_proveedores(request):
    total_proveedores = Proveedor.objects.count()
    proveedores_activos = Proveedor.objects.filter(estado=True).count()
    proveedores_bloqueados = total_proveedores - proveedores_activos

    percent_activos = (proveedores_activos / total_proveedores * 100) if total_proveedores else 0
    percent_bloqueados = 100 - percent_activos if total_proveedores else 0

    try:
        ultimo_proveedor = Proveedor.objects.latest('fecha_creacion')
    except ObjectDoesNotExist:
        ultimo_proveedor = None

    context = {
        'total_proveedores': total_proveedores,
        'percent_activos': round(percent_activos, 2),
        'percent_bloqueados': round(percent_bloqueados, 2),
        'ultimo_proveedor': ultimo_proveedor,
    }

    return render(request, 'administrador/dashboard_proveedores.html', context)



# ------------------------------------ FIN GESTIÓN DE PROVEEDORES ------------------------------------



# ------------------------------------  GESTIÓN DE COMPRAS ------------------------------------



# ------------------ LISTADO DE COMPRAS ACTIVAS Y BLOQUEADAS ------------------



@login_required
def lista_compras_activas(request):
    order_by = request.GET.get('order_by', '')

    compras_activas = Compra.objects.filter(activo=True)

    if order_by:
        if order_by == '':
            compras = compras_activas.order_by('')
        elif order_by == '':
            compras = compras_activas.order_by('')
        else:
            compras = compras_activas.order_by('')
    else:
        compras = compras_activas.order_by('-id')
    
    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')
    compras = paginator.get_page(page_number)

    return render(request, 'administrador/lista_compras.html', {'compras': compras, 'order_by': order_by})



@login_required
def lista_compras_bloqueadas(request):
    order_by = request.GET.get('order_by', '')

    compras_bloqueadas = Compra.objects.filter(activo=False)

    if order_by:
        if order_by == '':
            compras = compras_bloqueadas.order_by('')
        elif order_by == '':
            compras = compras_bloqueadas.order_by('')
        else:
            compras = compras_bloqueadas.order_by('')
    else:
        compras = compras_bloqueadas.order_by('-id') 

    paginator = Paginator(compras, 10)
    page_number = request.GET.get('page')
    compras = paginator.get_page(page_number)

    return render(request, 'administrador/lista_compras_bloqueadas.html', {'compras': compras, 'order_by': order_by})



# ------------------ AGREGAR - MOSTRAR - EDITAR - ACTIVAR - BLOQUEAR ------------------



@login_required
def registrar_compra_view(request):
    DetalleFormSet = formset_factory(DetalleCompraForm, extra=1, can_delete=True)
    
    proveedor_id = request.POST.get('proveedor') or request.GET.get('proveedor')
    proveedor = Proveedor.objects.filter(id=proveedor_id).first() if proveedor_id else None

    if request.method == 'POST' and 'submit' in request.POST:
        compra_form = CompraForm(request.POST)
        detalle_formset = DetalleFormSet(request.POST)

        for form in detalle_formset:
            form.fields['producto'].queryset = proveedor.productos.filter(activo=True) if proveedor else Producto.objects.none()

        if compra_form.is_valid() and detalle_formset.is_valid():
            productos_vistos = set()
            error_repetido = False

            formularios_validos = []

            for form in detalle_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    producto = form.cleaned_data['producto']

                    if producto in productos_vistos:
                        form.add_error('producto', 'Este producto ya fue ingresado.')
                        error_repetido = True
                    else:
                        productos_vistos.add(producto)
                        formularios_validos.append(form)
            if not formularios_validos:
                detalle_formset.non_form_errors = lambda: ['Debe agregar al menos un producto para registrar la compra.']
                return render(request, 'administrador/registrar_compra.html', {
                    'compra_form': compra_form,
                    'detalle_formset': detalle_formset,
                    'proveedor_seleccionado': proveedor,
                })

            productos_disponibles = proveedor.productos.filter(activo=True).count()
            if len(formularios_validos) > productos_disponibles:
                for form in detalle_formset:
                    form.add_error(None, "Se han ingresado más productos de los disponibles para este proveedor.")
                return render(request, 'administrador/registrar_compra.html', {
                    'compra_form': compra_form,
                    'detalle_formset': detalle_formset,
                    'proveedor_seleccionado': proveedor,
                })

            if error_repetido:
                return render(request, 'administrador/registrar_compra.html', {
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
                producto = form.cleaned_data['producto']
                cantidad = form.cleaned_data['cantidad']
                observaciones = form.cleaned_data.get('observaciones', '')

                DetalleCompra.objects.create(
                    compra=compra,
                    producto=producto,
                    cantidad=cantidad,
                    observaciones=observaciones
                )

                texto = f"- {producto.nombre}: {cantidad} unidades"
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

            return redirect('lista_compras_activas')

    else:
        compra_form = CompraForm(initial={'proveedor': proveedor_id})
        detalle_formset = DetalleFormSet()

        for form in detalle_formset:
            form.fields['producto'].queryset = proveedor.productos.filter(activo=True) if proveedor else Producto.objects.none()

    return render(request, 'administrador/registrar_compra.html', {
        'compra_form': compra_form,
        'detalle_formset': detalle_formset,
        'proveedor_seleccionado': proveedor,
    })




@csrf_exempt
def aprobar_compra(request):
    if request.method == 'POST':
        compra_id = request.POST.get('compra_id')
        compra = get_object_or_404(Compra, id=compra_id)

        if compra.estado != 'Pendiente':
            return JsonResponse({
                'success': False,
                'message': 'La compra ya fue procesada.'
            })

        compra.estado = 'Lista'
        compra.activo = False
        compra.save()

        numero_lote = str(uuid.uuid4())[:8]
        lote = Lote.objects.create(numero=numero_lote)

        for detalle in compra.detalles.all():
            producto = detalle.producto
            cantidad = detalle.cantidad

            DetalleLote.objects.create(
                lote=lote,
                producto=producto.nombre,
                cantidad=cantidad,
                precio=producto.precio
            )

            producto.cantidad += cantidad
            producto.lote = lote
            producto.save()

        return JsonResponse({
            'success': True,
            'message': 'Compra aprobada y lote creado correctamente.'
        })

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
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
    return render(request, 'administrador/detalle_compra.html', {'compra': compra})


# ------------------------------------ GESTIÓN DE PRODUCTOS ------------------------------------



def listar_productos(request):
    productos = Producto.objects.filter(activo=True)
    return render(request, 'administrador/listar_productos.html', {'productos': productos})

def productos_inactivos(request):
    productos = Producto.objects.filter(activo=False)
    return render(request, 'administrador/listar_productos_inactivos.html', {'productos': productos})

def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.activo = True
            fecha_actual = timezone.now().date()
            lote_actual, creado = Lote.objects.get_or_create(
                fecha=fecha_actual,
                defaults={'numero': fecha_actual.strftime('%Y%m%d'), 'activo': True}
            )
            producto.lote = lote_actual
            producto.save()
            return redirect('listar_productos')
    else:
        form = ProductoForm()
    return render(request, 'administrador/form_producto.html', {'form': form, 'titulo': 'Agregar Producto'})

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('listar_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'administrador/form_producto.html', {'form': form, 'titulo': 'Editar Producto'})

def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    return redirect('listar_productos')

def toggle_estado_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.activo = not producto.activo
    producto.save()
    if producto.activo:
        messages.success(request, "Producto activado con éxito.")
    else:
        messages.warning(request, "Producto desactivado con éxito.")
    origen = request.GET.get('origen', 'activos')
    return redirect('productos_inactivos' if origen == 'inactivos' else 'listar_productos')

def ver_lotes_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    lotes = Lote.objects.filter(producto=producto)  # ajusta según tu modelo
    return render(request, 'administrador/lotes_por_producto.html', {
        'producto': producto,
        'lotes': lotes,
    })

def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    return redirect('listar_productos')



# ------------------------------------ GESTIÓN DE LOTES ------------------------------------



def listar_lotes(request):
    lotes = Lote.objects.filter(activo=True).order_by('-fecha')
    return render(request, 'administrador/listar_lotes.html', {'lotes': lotes})


def ver_lote(request, id):
    lote = get_object_or_404(Lote, id=id)
    detalles = DetalleLote.objects.filter(lote=lote)

    return render(request, 'administrador/ver_lote.html', {
        'lote': lote,
        'detalles': detalles
    })



def eliminar_lote(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)
    lote.delete()
    messages.success(request, 'Lote eliminado correctamente.')
    return redirect('listar_lotes')



def carga_excel_lotes(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        df_raw = pd.read_excel(archivo, header=None)

        columnas_esperadas = {'producto', 'cantidad', 'precio'}
        indice_inicio = None

        for i, fila in df_raw.iterrows():
            columnas_actuales = set()
            for celda in fila:
                if pd.notna(celda):
                    valor = str(celda).strip().lower()
                    if valor.endswith('s'):
                        valor = valor[:-1]
                    columnas_actuales.add(valor)

            if columnas_esperadas.issubset(columnas_actuales):
                indice_inicio = i
                break

        if indice_inicio is None:
            messages.error(request, 'No se encontraron columnas válidas: producto, cantidad, precio.')
            return redirect('listar_lotes')

        df = pd.read_excel(archivo, header=indice_inicio)
        df.columns = [str(c).strip().lower().rstrip('s') for c in df.columns]

        fecha_actual = timezone.now().date()
        lote_existente = Lote.objects.filter(fecha=fecha_actual).first()

        if lote_existente:
            lote = lote_existente
        else:
            # Contar cuántos días únicos hay registrados
            dias_registrados = Lote.objects.values_list('fecha', flat=True).distinct().count()
            numero_lote = f"L-{dias_registrados + 1:03d}"
            
            lote = Lote.objects.create(
                numero=f"L-{numero_lote}",
                fecha=fecha_actual
            )


        for _, row in df.iterrows():
            try:
                producto_nombre = str(row['producto']).strip()
                cantidad = int(row['cantidad'])
                precio = float(row['precio'])

                producto = Producto.objects.filter(nombre__iexact=producto_nombre).first()
                if not producto:
                    producto = Producto.objects.create(
                        nombre=producto_nombre,
                        cantidad=cantidad,
                        tipo='Automático',
                        precio=precio
                    )

                producto, _ = Producto.objects.get_or_create(nombre=producto_nombre)

                DetalleLote.objects.create(
                    lote=lote,
                    producto=producto.nombre,  
                    cantidad=cantidad,
                    precio=precio
)

            except Exception:
                continue  

        messages.success(request, 'Lote cargado exitosamente.')
        return redirect('listar_lotes')

    return redirect('listar_lotes')



# ------------------------------------ GESTIÓN DE MERMAS ------------------------------------



def listar_mermas(request):
    mermas = Merma.objects.filter(activo=True)
    return render(request, 'administrador/listar_mermas.html', {'mermas': mermas})

def agregar_merma(request):
    if request.method == 'POST':
        form = MermaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_mermas')
    else:
        form = MermaForm()
    return render(request, 'administrador/form_merma.html', {'form': form, 'titulo': 'Agregar Merma'})



# ------------------------------------ GESTIÓN DE CLIENTES ------------------------------------



def listar_clientes_activos(request):
    clientes = Cliente.objects.filter(activo=True)
    return render(request, 'administrador/listar_clientes_activos.html', {'clientes': clientes})

def listar_clientes_inactivos(request):
    clientes = Cliente.objects.filter(activo=False)
    return render(request, 'administrador/listar_clientes_inactivos.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.activo = True
            cliente.save()

            return redirect('listar_clientes_activos')  
    else:
        form = ClienteForm()
    
    return render(request, 'administrador/crear_cliente.html', {'form': form})

def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.delete()
    return redirect('listar_clientes_activos')

def toggle_estado_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.activo = not cliente.activo  
    cliente.save()

    if cliente.activo:
        return redirect('listar_clientes_inactivos')
    else:
        return redirect('listar_clientes_activos')
    
def ranking_clientes(request):
    return render(request, 'administrador/ranking_clientes.html') 

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
    return render(request, 'administrador/dashboard_clientes.html', context)


def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes_activos')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'administrador/editar_clientes.html', {'form': form})




def dashboard_productos(request):
    total_productos = Producto.objects.count()
    activos = Producto.objects.filter(activo=True).count()
    inactivos = total_productos - activos
    productos_con_merma = Merma.objects.values('producto').distinct().count()
    porcentaje_mermas = (productos_con_merma / total_productos * 100) if total_productos else 0
    tipos_data = Producto.objects.values('tipo').annotate(total=Count('id'))

    try:
        ultimo_producto = Producto.objects.latest('fecha')
    except ObjectDoesNotExist:
        ultimo_producto = None

    context = {
        'total_productos': total_productos,
        'percent_activos': round((activos / total_productos) * 100) if total_productos else 0,
        'percent_inactivos': round((inactivos / total_productos) * 100) if total_productos else 0,
        'percent_mermas': round(porcentaje_mermas),
        'tipos': [tipo['tipo'] for tipo in tipos_data],
        'cantidades': [tipo['total'] for tipo in tipos_data],
        'ultimo_producto': ultimo_producto,
    }
    return render(request, 'administrador/dashboard_productos.html', context)

def debug_url_test(request):
    try:
        url = reverse('eliminar_producto', kwargs={'id': 1})
        return HttpResponse(f"✅ URL encontrada: {url}")
    except Exception as e:
        return HttpResponse(f"❌ Error: {e}")
    

# ------------------------------------ GESTIÓN DE VENTAS ------------------------------------



def dashboard_ventas(request):
    total_ventas = Venta.objects.count()
    ventas_dia = Venta.objects.filter(fecha=timezone.now().date()).count()
    productos_vendidos = sum(v.cantidad_total for v in Venta.objects.all())

    categorias_ventas = ['Perfumes', 'Cremas', 'Accesorios']  # ejemplo
    montos_ventas = [100000, 50000, 25000]  # ejemplo
    medios_pago = ['Efectivo', 'Tarjeta', 'Transferencia']
    pagos = [60, 25, 15]  # ejemplo

    ultima_venta = Venta.objects.last()

    context = {
        'total_ventas': total_ventas,
        'ventas_dia': ventas_dia,
        'productos_vendidos': productos_vendidos,
        'categorias_ventas': categorias_ventas,
        'montos_ventas': montos_ventas,
        'medios_pago': medios_pago,
        'pagos': pagos,
        'ultima_venta': ultima_venta
    }

    return render(request, 'administrador/dashboard_ventas.html', context)


def listar_ventas(request):
    ventas = Venta.objects.all()
    return render(request, 'administrador/listar_ventas.html', {'ventas': ventas})