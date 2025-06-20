from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
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
from registration.models import Profile, Proveedor, Compra, Producto, DetalleCompra, DetalleLote, Lote, Cliente, ProductoUnidad, Merma, DetalleVenta
from datetime import datetime, date
from django.core.exceptions import ValidationError
from django.contrib import messages
from administrador.forms import EditUserProfileForm, CrearProveedorForm, EditarProveedorForm, CompraForm, DetalleCompraForm, CargaMasivaProveedorForm 
from administrador.forms import CargaMasivaUsuariosForm, AprobarCompraForm, ProductoForm, ProductoUnidadFormSet, ProductoUnidadForm, EditarProductoForm, LoteForm
from administrador.forms import DetalleLoteForm, BaseDetalleLoteFormSet, VentaForm, DetalleVentaFormSet, DetalleVentaForm
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
from django.db.models import Count, Sum, F, Q,  ExpressionWrapper, FloatField
from django.contrib import messages
from .forms import ProductoForm
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
    


# ------------------ ACTUALIZAR CREDENCIALES ------------------



def generar_password_aleatoria(longitud=10):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))

def cambiar_credenciales(request, user_id):
    if request.method == 'POST':
        admin_password = request.POST.get('admin_password')
        confirm_text = request.POST.get('confirm_text')
        usuario_objetivo = get_object_or_404(User, id=user_id)

        if not request.user.is_superuser:
            messages.error(request, "No tiene permisos para realizar esta acción.")
            return redirect('mostrar_usuario', user_id)

        user_auth = authenticate(username=request.user.username, password=admin_password)
        if not user_auth:
            messages.error(request, "Contraseña de administrador incorrecta.")
            return redirect('mostrar_usuario', user_id)

        if confirm_text.strip().lower() != "confirmar":
            messages.error(request, "Debe escribir 'confirmar' para continuar.")
            return redirect('mostrar_usuario', user_id)

        # Generar y asignar nueva contraseña
        nueva_password = generar_password_aleatoria()
        usuario_objetivo.set_password(nueva_password)
        usuario_objetivo.save()

        # Enviar correo con nuevas credenciales
        send_mail(
            subject='Actualización de credenciales',
            message=(
                f'Hola usuario {usuario_objetivo.first_name},\n\n'
                f'Le informamos que su contraseña ha sido actualizada recientemente por un administrador.\n'
                f'Su nombre de usuario en caso de que lo haya olvidado es: {usuario_objetivo.username}\n'
                f'Su nueva contraseña es: {nueva_password}\n\n'
                'Por favor, inicie sesión y cámbiela lo antes posible.\n'
                f'Equipo ComercialJM\n'
            ),
            from_email='noreply@tusistema.com',
            recipient_list=[usuario_objetivo.email],
            fail_silently=False
        )

        messages.success(request, "Contraseña actualizada y enviada por correo.")
        return redirect('mostrar_usuario', user_id)
    


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


def carga_masiva_usuarios(request):
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']

        try:
            df = pd.read_excel(archivo)

            campos_requeridos = [
                'rut', 'first_name', 'last_name', 'sexo', 'correo',
                'telefono', 'direccion', 'fecha_nacimiento', 'cargo'
            ]
            for campo in campos_requeridos:
                if campo not in df.columns:
                    messages.error(request, f"Falta la columna: {campo}")
                    return redirect('lista_usuarios_activos')

            usuarios_creados = 0
            usuarios_omitidos = 0

            for index, row in df.iterrows():
                fila = index + 2

                try:
                    rut = str(row['rut']).strip()
                    first_name = str(row['first_name']).strip()
                    last_name = str(row['last_name']).strip()
                    sexo = str(row['sexo']).strip().upper()
                    correo = str(row['correo']).strip()
                    telefono = str(row['telefono']).strip()
                    direccion = str(row['direccion']).strip()
                    cargo = str(row['cargo']).strip()

                    # Validar RUT
                    if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', rut):
                        messages.warning(request, f"Fila {fila}: RUT inválido (formato esperado XX.XXX.XXX-X)")
                        usuarios_omitidos += 1
                        continue

                    # Validar nombres
                    if not re.match(r'^([A-Za-zÁÉÍÓÚáéíóúÑñ]+(\s)?){1,3}$', first_name):
                        messages.warning(request, f"Fila {fila}: Nombre inválido (solo letras, máximo 3 palabras)")
                        usuarios_omitidos += 1
                        continue

                    # Validar apellidos
                    if not re.match(r'^([A-Za-zÁÉÍÓÚáéíóúÑñ]+(\s)?){1,2}$', last_name):
                        messages.warning(request, f"Fila {fila}: Apellido inválido (solo letras, máximo 2 palabras)")
                        usuarios_omitidos += 1
                        continue

                    # Validar sexo
                    if sexo not in ['M', 'F']:
                        messages.warning(request, f"Fila {fila}: Sexo inválido (solo 'M' o 'F')")
                        usuarios_omitidos += 1
                        continue

                    # Validar correo
                    try:
                        validate_email(correo)
                    except ValidationError:
                        messages.warning(request, f"Fila {fila}: Correo inválido")
                        usuarios_omitidos += 1
                        continue

                    # Validar teléfono
                    if not re.match(r'^\d\s\d{4}\s\d{4}$', telefono):
                        messages.warning(request, f"Fila {fila}: Teléfono inválido (formato esperado: 9 1234 5678)")
                        usuarios_omitidos += 1
                        continue

                    # Validar cargo
                    if cargo not in ['Empleado', 'Administrador']:
                        messages.warning(request, f"Fila {fila}: Cargo inválido (solo 'Empleado' o 'Administrador')")
                        usuarios_omitidos += 1
                        continue

                    # Validar existencia
                    if Profile.objects.filter(rut=rut).exists() or User.objects.filter(username=rut).exists():
                        messages.warning(request, f"Fila {fila}: Usuario con ese RUT ya existe")
                        usuarios_omitidos += 1
                        continue

                    # Fecha de nacimiento
                    fecha_raw = row['fecha_nacimiento']
                    if pd.isna(fecha_raw):
                        fecha_nacimiento = None
                    elif isinstance(fecha_raw, str):
                        fecha_nacimiento = parse_date(fecha_raw)
                    else:
                        fecha_nacimiento = pd.to_datetime(fecha_raw).date()

                    # Crear usuario
                    password = get_random_string(12)
                    user = User(
                        username=rut,
                        first_name=first_name,
                        last_name=last_name,
                        email=correo
                    )
                    user.set_password(password)
                    user.save()

                    # Crear perfil
                    profile = Profile.objects.create(
                        user=user,
                        rut=rut,
                        telefono=telefono,
                        fecha_nacimiento=fecha_nacimiento,
                        direccion=direccion,
                        sexo=sexo
                    )

                    grupo, _ = Group.objects.get_or_create(name=cargo)
                    profile.groups.add(grupo)

                    usuarios_creados += 1

                except Exception as e:
                    messages.warning(request, f"Fila {fila}: Error inesperado - {str(e)}")
                    usuarios_omitidos += 1
                    continue

            messages.success(
                request,
                f"Carga completada. {usuarios_creados} usuarios creados, {usuarios_omitidos} filas omitidas por errores."
            )

        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar el archivo: {str(e)}")

        return redirect('lista_usuarios_activos')

    return redirect('lista_usuarios_activos')




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



# ------------------------------------ CARGA MASIVA DE PROVEEDORES ------------------------------------



@login_required
@require_POST
@require_POST
def carga_masiva_proveedores(request):
    form = CargaMasivaProveedorForm(request.POST, request.FILES)

    if form.is_valid():
        archivo = request.FILES['archivo']
        try:
            # Leer archivo
            if archivo.name.endswith('.xlsx'):
                df = pd.read_excel(archivo)
            elif archivo.name.endswith('.csv'):
                df = pd.read_csv(archivo)
            else:
                messages.error(request, "Formato no soportado. Usa .xlsx o .csv.")
                return redirect('lista_proveedores_activos')

            columnas_requeridas = ['nombre', 'rut', 'telefono', 'correo', 'direccion']
            if not all(col in df.columns for col in columnas_requeridas):
                messages.error(request, "Faltan columnas requeridas.")
                return redirect('lista_proveedores_activos')

            errores, nuevos = [], 0

            for index, row in df.iterrows():
                fila = index + 2  # Excel: fila 1 = encabezado

                nombre = str(row['nombre']).strip()
                rut = str(row['rut']).strip()
                telefono = str(row.get('telefono', '')).strip()
                correo = str(row['correo']).strip()
                direccion = str(row.get('direccion', '')).strip()

                # Validaciones personalizadas
                if not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", rut):
                    errores.append(f"Fila {fila}: RUT inválido ({rut}). Formato: XX.XXX.XXX-X")
                    continue

                if Proveedor.objects.filter(rut=rut).exists():
                    errores.append(f"Fila {fila}: RUT {rut} ya está registrado.")
                    continue

                if re.search(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]", nombre):
                    errores.append(f"Fila {fila}: Nombre inválido. Solo letras y espacios.")
                    continue

                if not re.match(r"^\d\s\d{4}\s\d{4}$", telefono):
                    errores.append(f"Fila {fila}: Teléfono inválido ({telefono}). Formato: 9 8765 4321")
                    continue

                if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", correo):
                    errores.append(f"Fila {fila}: Correo inválido ({correo})")
                    continue

                # Crear proveedor
                proveedor = Proveedor(
                    nombre=nombre,
                    rut=rut,
                    telefono=telefono,
                    correo=correo,
                    direccion=direccion,
                    estado=True
                )
                proveedor.save()
                nuevos += 1

            if nuevos:
                messages.success(request, f"{nuevos} proveedores cargados correctamente.")
            if errores:
                for e in errores:
                    messages.warning(request, e)

        except Exception as e:
            messages.error(request, f"Error al procesar archivo: {str(e)}")
    else:
        messages.error(request, "Formulario inválido. Sube un archivo válido.")

    return redirect('lista_proveedores_activos')



# ------------------------------------ FIN GESTIÓN DE PROVEEDORES ------------------------------------



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

    return render(request, 'administrador/lista_compras.html', {'compras': compras, 'order_by': order_by})



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

    return render(request, 'administrador/lista_compras_bloqueadas.html', {'compras': compras, 'order_by': order_by})



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
            return render(request, 'administrador/registrar_compra.html', {
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
                return render(request, 'administrador/registrar_compra.html', {
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

            return redirect('lista_compras_activas')

    else:
        compra_form = CompraForm(initial={'proveedor': proveedor_id})
        detalle_formset = DetalleFormSet()

        for form in detalle_formset:
            form.fields['producto_unidad'].queryset = ProductoUnidad.objects.filter(
                producto__proveedores=proveedor,
                producto__activo=True
            ) if proveedor else ProductoUnidad.objects.none()

    return render(request, 'administrador/registrar_compra.html', {
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
    return render(request, 'administrador/detalle_compra.html', {'compra': compra})



# ------------------ DASHBOARD DE COMPRAS ------------------




@login_required
def dashboard_compras(request):
    ultima_compra = Compra.objects.order_by('-fecha').first()

    proveedor_mas_compras = (
        Compra.objects.values('proveedor__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )

    estado_data_raw = Compra.objects.values('estado').annotate(cantidad=Count('estado'))
    estado_data = {}

    for estado in estado_data_raw:
        nombre_estado = estado['estado'].capitalize()
        estado_data[nombre_estado] = estado['cantidad']

    total_estados = sum(estado_data.values())

    orden_deseado = ['Pendiente', 'Lista', 'Cancelada']
    colores_estado = {
        'Pendiente': 'yellow',
        'Lista': 'green',
        'Cancelada': 'red',
    }

    estado_chart_data = []
    for estado in orden_deseado:
        porcentaje = round((estado_data.get(estado, 0) / total_estados) * 100, 2) if total_estados > 0 else 0
        estado_chart_data.append({
            'estado': estado,
            'porcentaje': porcentaje,
            'color': colores_estado.get(estado, '#ccc'),
        })

    # Top productos
    top_productos = (
        DetalleCompra.objects
        .values('producto_unidad__producto__nombre')
        .annotate(total_cantidad=Count('id'))
        .order_by('-total_cantidad')[:3]
    )

    context = {
        'ultima_compra': ultima_compra,
        'proveedor_mas_compras': proveedor_mas_compras,
        'estado_chart_data': estado_chart_data,
        'top_productos': top_productos,
    }

    return render(request, 'administrador/dashboard_compras.html', context)


# ------------------------------------ GESTIÓN DE PRODUCTOS ------------------------------------




@login_required
def listar_productos(request):
    order_by = request.GET.get('order_by', '')

    productos_activos = Producto.objects.filter(activo=True)

    if order_by:
        if order_by == 'nombre':
            productos = productos_activos.order_by('nombre')
        elif order_by == 'tipo':
            productos = productos_activos.order_by('tipo')
        else:
            productos = productos_activos
    else:
        productos = productos_activos

    paginator = Paginator(productos, 10)  # 10 productos por página
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    return render(request, 'administrador/listar_productos.html', {
        'productos': productos,
        'order_by': order_by
    })

def productos_inactivos(request):
    productos = Producto.objects.filter(activo=False)
    return render(request, 'administrador/listar_productos_inactivos.html', {'productos': productos})



def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto_obj = form.save(commit=False)

            formset = ProductoUnidadFormSet(request.POST, instance=producto_obj)
            if formset.is_valid():
              
                producto_obj.save()
                formset.save()
                return redirect('listar_productos') 
        else:
            
            formset = ProductoUnidadFormSet(request.POST)
    else:
        form = ProductoForm()
        formset = ProductoUnidadFormSet()

    return render(request, 'administrador/form_producto.html', {
        'form': form,
        'formset': formset,
    })


from django.shortcuts import get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone



def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    ProductoUnidadFormSet = inlineformset_factory(
        Producto,
        ProductoUnidad,
        form=ProductoUnidadForm,
        extra=0,
        can_delete=True,
        min_num=1,
        validate_min=True,
        max_num=3,
        validate_max=True,
    )

    if request.method == 'POST':
        form = EditarProductoForm(request.POST, instance=producto)
        formset = ProductoUnidadFormSet(request.POST, instance=producto)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('listar_productos')
    else:
        form = EditarProductoForm(instance=producto)
        formset = ProductoUnidadFormSet(instance=producto)

    return render(request, 'administrador/form_editar_producto.html', {
        'form': form,
        'formset': formset,
        'titulo': 'Editar Producto'
    })



def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    unidades = producto.unidades.all()

    detalle_stock = []
    for unidad in unidades:
        cantidad_total = (
            unidad.detallelote_set.filter(lote__activo=True)
            .aggregate(total_cantidad=Sum('cantidad'))['total_cantidad'] or 0
        )

        detalle_stock.append({
            'unidad_medida': unidad.get_unidad_medida_display(),
            'precio': unidad.precio,
            'cantidad_total': cantidad_total,
        })

    context = {
        'producto': producto,
        'detalle_stock': detalle_stock,
    }
    return render(request, 'administrador/detalle_producto.html', context)


@require_POST
def bloquear_productos(request):
    ids = request.POST.get('ids', '')
    id_list = [int(i) for i in ids.split(',') if i.isdigit()]
    Producto.objects.filter(id__in=id_list).update(activo=False)
    return redirect('listar_productos')


@require_POST
@login_required
def activar_productos(request):
    try:
        producto_id = request.POST.get('producto_id')
        producto_ids = json.loads(request.POST.get('producto_ids', '[]')) if request.POST.get('producto_ids') else []

        if producto_id:
            producto_ids = [int(producto_id)]

        producto_ids = [int(uid) for uid in producto_ids]
        productos = Producto.objects.filter(id__in=producto_ids, activo=False)

        updated_count = 0
        for producto in productos:
            producto.activo = True
            producto.save()
            updated_count += 1

        return JsonResponse({'success': True, 'updated': updated_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def listar_productos_bloqueados(request):
    order_by = request.GET.get('order_by', '')

    productos_bloqueados = Producto.objects.filter(activo=False)

    if order_by:
        if order_by == 'nombre':
            productos = productos_bloqueados.order_by('nombre')
        elif order_by == 'tipo':
            productos = productos_bloqueados.order_by('tipo')
        else:
            productos = productos_bloqueados
    else:
        productos = productos_bloqueados

    paginator = Paginator(productos, 10)  # 10 productos por página
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    return render(request, 'administrador/listar_productos_inactivos.html', {
        'productos': productos,
        'order_by': order_by
    })




# ------------------------------------ GESTIÓN DE LOTES ------------------------------------

@login_required
def agregar_lote(request):
    DetalleLoteFormSet = modelformset_factory(
        DetalleLote,
        form=DetalleLoteForm,
        formset=BaseDetalleLoteFormSet,
        extra=1,
        can_delete=True,
    )

    lote_form = LoteForm(request.POST or None)
    formset = DetalleLoteFormSet(request.POST or None, queryset=DetalleLote.objects.none())

    if request.method == 'POST':
        if lote_form.is_valid() and formset.is_valid():
            lote = lote_form.save(commit=False)
            lote.save()

            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                    detalle = form.save(commit=False)
                    detalle.lote = lote
                    detalle.save()
            return redirect('listar_lotes')

    return render(request, 'administrador/agregar_lote.html', {
        'lote_form': lote_form,
        'formset': formset,
    })


@login_required
def listar_lotes(request):
    order_by = request.GET.get('order_by', '-id')
    lotes_activos = Lote.objects.filter(activo=True)

    if order_by == 'id':
        lotes = lotes_activos.order_by('id')
    else:
        lotes = lotes_activos.order_by('-id')

    paginator = Paginator(lotes, 10)
    page_number = request.GET.get('page')
    lotes = paginator.get_page(page_number)

    return render(request, 'administrador/listar_lotes.html', {
        'lotes': lotes,
        'order_by': order_by
    })


def ver_lote(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id, activo=True)

    detalles = lote.detalles.select_related('producto_unidad__producto')

    detalle_lote = []
    for detalle in detalles:
        detalle_lote.append({
            'producto': detalle.producto_unidad.producto.nombre,
            'unidad': detalle.producto_unidad.get_unidad_medida_display(),
            'precio': detalle.producto_unidad.precio,
            'cantidad': detalle.cantidad,
            'fecha': lote.fecha,
            'numero': lote.id,
        })

    context = {
        'detalle_lote': detalle_lote,
        'lote': lote,
    }

    return render(request, 'administrador/ver_lote.html', context)





# ------------------------------------ GESTIÓN DE MERMAS ------------------------------------





@login_required
def listar_mermas(request):
    order_by = request.GET.get('order_by', '-id')

    mermas_activos = Merma.objects.all()

    if order_by:
        if order_by == 'id':
            mermas = mermas_activos.order_by('id')
        elif order_by == 'lote':
            mermas = mermas_activos.order_by('lote')
        else:
            mermas = mermas_activos.order_by('-id')
    else:
        mermas = mermas_activos.order_by('-id')

    paginator = Paginator(mermas, 10)
    page_number = request.GET.get('page')
    mermas = paginator.get_page(page_number)

    return render(request, 'administrador/listar_mermas.html', {
        'mermas': mermas,
        'order_by': order_by
    })

from .forms import MermaForm, MotivoMermaForm

@login_required
def registrar_merma(request):
    MermaFormSet = modelformset_factory(Merma, form=MermaForm, extra=1, can_delete=False)
    formset = MermaFormSet(request.POST or None, queryset=Merma.objects.none())
    motivo_form = MotivoMermaForm(request.POST or None)

    if request.method == 'POST':
        for form in formset:
            form.empty_permitted = False

        if formset.is_valid() and motivo_form.is_valid():
            motivo = motivo_form.cleaned_data['motivo']
            for form in formset:
                merma = form.save(commit=False)
                merma.motivo = motivo
                merma.save()

                # Descontar stock del lote correspondiente
                detalle = DetalleLote.objects.get(
                    producto_unidad=merma.producto_unidad,
                    lote=merma.lote
                )
                detalle.cantidad -= merma.cantidad
                detalle.save()

            return redirect('listar_mermas')

    return render(request, 'administrador/registrar_merma.html', {
        'formset': formset,
        'motivo_form': motivo_form
    })

@login_required
def detalle_merma(request, merma_id):
    merma = get_object_or_404(Merma, id=merma_id)

    contexto = {
        'merma': merma
    }

    return render(request, 'administrador/detalle_merma.html', contexto)

@login_required
def deshacer_merma(request, merma_id):
    merma = get_object_or_404(Merma, id=merma_id)

    if merma.lote and merma.producto_unidad:
        try:
            detalle = DetalleLote.objects.get(lote=merma.lote, producto_unidad=merma.producto_unidad)
            detalle.cantidad += merma.cantidad
            detalle.save()
        except DetalleLote.DoesNotExist:
            messages.error(request, "No se pudo encontrar el stock para restaurar.")
            return redirect('listar_mermas')

    merma.delete()
    messages.success(request, "La merma fue deshecha correctamente.")
    return redirect('listar_mermas')




# ------------------------------------ GESTIÓN DE CLIENTES ------------------------------------



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

    return render(request, 'administrador/listar_clientes_activos.html', {
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
        'administrador/listar_clientes_inactivos.html',
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
            return redirect('listar_clientes_activos')
        else:
            print("Errores del formulario:", form.errors) 
    else:
        form = ClienteForm()

    return render(request, 'administrador/crear_cliente.html', {'form': form})
    

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

    return render(request, 'administrador/ranking_clientes.html', {
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


from django.db.models import Prefetch
def detalle_compras_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    ventas = Venta.objects.filter(cliente=cliente).prefetch_related(
        Prefetch('detalles', queryset=DetalleVenta.objects.select_related('producto_unidad__producto'))
    )

    return render(request, 'administrador/detalle_compras_cliente.html', {
        'cliente': cliente,
        'ventas': ventas
    })


# ------------------------------------ GESTIÓN DE PRODUCTOS ------------------------------------


def dashboard_productos(request):
    total_productos = Producto.objects.count()
    activos = Producto.objects.filter(activo=True).count()
    inactivos = total_productos - activos
    productos_con_merma = Merma.objects.values('producto_unidad__producto').distinct().count()
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


    

# ------------------------------------ GESTIÓN DE VENTAS ------------------------------------



def dashboard_ventas(request):
    total_ventas = Venta.objects.filter(activo=True).aggregate(total=Sum('total'))['total'] or 0

    hoy = now().date()
    ventas_dia = Venta.objects.filter(fecha__date=hoy, activo=True).aggregate(total=Sum('total'))['total'] or 0

    productos_vendidos = DetalleVenta.objects.filter(venta__activo=True).aggregate(total=Sum('cantidad'))['total'] or 0

    ventas_por_categoria_qs = DetalleVenta.objects.filter(
        venta__activo=True
    ).select_related('producto_unidad__producto').values(
        'producto_unidad__producto__tipo'
    ).annotate(
        total_vendido=Sum(F('cantidad') * F('producto_unidad__precio'))
    ).order_by('producto_unidad__producto__tipo')

    categorias_ventas = [item['producto_unidad__producto__tipo'] for item in ventas_por_categoria_qs]
    montos_ventas = [float(item['total_vendido'] or 0) for item in ventas_por_categoria_qs]

    medios_pago_qs = Venta.objects.filter(activo=True).values('metodo_pago').annotate(
        cantidad=Count('id')
    )
    labels_pago = [item['metodo_pago'] for item in medios_pago_qs]
    medios_pago = [item['cantidad'] for item in medios_pago_qs]

    ultima_venta_obj = Venta.objects.filter(activo=True).order_by('-fecha').first()
    if ultima_venta_obj:
        ultima_venta = {
            'cliente_nombre': ultima_venta_obj.cliente.nombre if ultima_venta_obj.cliente else "Sin cliente",
            'fecha': ultima_venta_obj.fecha
        }
    else:
        ultima_venta = {
            'cliente_nombre': 'N/A',
            'fecha': None
        }

    context = {
        'total_ventas': total_ventas,
        'ventas_dia': ventas_dia,
        'productos_vendidos': productos_vendidos,
        'categorias_ventas': categorias_ventas,
        'montos_ventas': montos_ventas,
        'labels_pago': labels_pago,
        'medios_pago': medios_pago,
        'ultima_venta': ultima_venta,
    }
    return render(request, 'administrador/dashboard_ventas.html', context)


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

    return render(request, 'administrador/listar_ventas.html', {
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
                    return render(request, 'administrador/registrar_venta.html', {
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
                        return render(request, 'administrador/registrar_venta.html', {
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

                return redirect('listar_ventas')

            else:
                return render(request, 'administrador/registrar_venta.html', {
                    'venta_form': venta_form,
                    'formset': formset,
                    'stock_map_json': json.dumps(stock_map),
                    'price_map_json': json.dumps(price_map),
                    'clientes_info_json': json.dumps(clientes_info),
                })
        else:
            formset = DetalleVentaFormSet(instance=Venta())
            return render(request, 'administrador/registrar_venta.html', {
                'venta_form': venta_form,
                'formset': formset,
                'stock_map_json': json.dumps(stock_map),
                'price_map_json': json.dumps(price_map),
                'clientes_info_json': json.dumps(clientes_info),
            })

    else:
        venta_form = VentaForm()
        formset = DetalleVentaFormSet(instance=Venta())
        return render(request, 'administrador/registrar_venta.html', {
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

    html_string = render_to_string('administrador/boleta_pdf.html', {
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

    html_string = render_to_string('administrador/factura_pdf.html', {
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
        return redirect('listar_ventas')

    venta.delete()
    messages.success(request, "La venta fue deshecha correctamente y el stock fue restaurado.")
    return redirect('listar_ventas')


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
    return render(request, 'administrador/detalle_venta.html', context)


# ------------------------------------ REPORTERIA ------------------------------------

def reporteria_view(request):

    usuarios = User.objects.filter(is_active=True)

    productos_unidad_totales = ProductoUnidad.objects.filter(producto__activo=True)

    productos_unidad_totales = productos_unidad_totales.annotate(
        cantidad_total=Sum('detallelote__cantidad')
    ).order_by('producto__nombre', 'unidad_medida')

    productos = []
    for pu in productos_unidad_totales:
        productos.append({
            'nombre': f"{pu.producto.nombre} ({pu.unidad_medida})",
            'cantidad': pu.cantidad_total or 0
        })

    compras_qs = Compra.objects.filter(activo=False, estado='Lista')
    ventas_qs = Venta.objects.all()
    mermas_qs = Merma.objects.all()

    compras_cantidad = compras_qs.count()
    ventas_cantidad = ventas_qs.count()
    mermas_cantidad = mermas_qs.count()

    compras_total = compras_qs.aggregate(total=Sum('total'))['total'] or 0
    ventas_total = ventas_qs.aggregate(total=Sum('total'))['total'] or 0
    mermas_total = sum([merma.precio * merma.cantidad for merma in mermas_qs])

    usuarios_activos = User.objects.filter(is_active=True).order_by('username')
    compras_por_usuario = []
    for usuario in usuarios_activos:
        user_compras = compras_qs.filter(usuario=usuario).count()
        compras_por_usuario.append({
            'username': usuario.username,
            'compras': user_compras
        })

    ventas_por_usuario = []
    for usuario in usuarios_activos:
        user_ventas = ventas_qs.filter(usuario=usuario).count()
        ventas_por_usuario.append({
            'username': usuario.username,
            'ventas': user_ventas
        })

    context = {
        'productos': productos,
        'data_cantidad': {
            'compras': compras_cantidad,
            'ventas': ventas_cantidad,
            'mermas': mermas_cantidad,
        },
        'data_total': {
            'compras': float(compras_total),
            'ventas': float(ventas_total),
            'mermas': float(mermas_total),
        },
        'compras_por_usuario': compras_por_usuario,
        'ventas_por_usuario': ventas_por_usuario,
    }

    return render(request, 'administrador/reporteria.html', context)



def reporteria_pdf_view(request):
    # Recolección de datos
    cantidad_compras = Compra.objects.filter(estado='Lista').count()
    cantidad_ventas = Venta.objects.count()
    cantidad_mermas = Merma.objects.count()

    total_compras = Compra.objects.filter(estado='Lista').aggregate(total=Sum('total'))['total'] or 0
    total_ventas = Venta.objects.aggregate(total=Sum('total'))['total'] or 0
    total_mermas = Merma.objects.aggregate(
        total=Sum(ExpressionWrapper(F('precio') * F('cantidad'), output_field=FloatField()))
    )['total'] or 0

    productos_con_lotes = ProductoUnidad.objects.annotate(
        total_cantidad=Sum('detallelote__cantidad'),
        subtotal=ExpressionWrapper(
            F('precio') * Coalesce(Sum('detallelote__cantidad'), 0),
            output_field=FloatField()
        )
    ).select_related('producto').order_by('producto__nombre', 'unidad_medida')

    compras_por_usuario = User.objects.annotate(total_compras=Count('compras'))
    ventas_por_usuario  = User.objects.annotate(total_ventas=Count('ventas'))

    # Obtener imágenes base64 del POST
    img_productos        = request.POST.get('img_productos')
    img_torta_cantidad   = request.POST.get('img_torta_cantidad')
    img_torta_total      = request.POST.get('img_torta_total')
    img_compras_usuario  = request.POST.get('img_compras_usuario')
    img_ventas_usuario   = request.POST.get('img_ventas_usuario')

    context = {
        'cantidad_compras': cantidad_compras,
        'cantidad_ventas': cantidad_ventas,
        'cantidad_mermas': cantidad_mermas,
        'total_compras': total_compras,
        'total_ventas': total_ventas,
        'total_mermas': total_mermas,
        'productos_con_lotes': productos_con_lotes,
        'compras_por_usuario': compras_por_usuario,
        'ventas_por_usuario': ventas_por_usuario,
        'img_productos': img_productos,
        'img_torta_cantidad': img_torta_cantidad,
        'img_torta_total': img_torta_total,
        'img_compras_usuario': img_compras_usuario,
        'img_ventas_usuario': img_ventas_usuario,
    }

    template = get_template('administrador/reporteria_pdf.html')
    html_body = template.render(context)

    css_override = """
    <style>
      img {
        display: block;
        max-width: 100% !important;
        width: 100% !important;
        height: auto !important;
      }
      /* 1ª imagen (Productos): altura fija más grande */
      img:nth-of-type(1) {
        height: 600px !important;
      }
    </style>
    """

    html = HTML(string=css_override + html_body, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporteria.pdf"'
    return response